import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import {
  Code,
  Download,
  Copy,
  CheckCircle,
  AlertCircle,
  Loader2,
  Zap,
  FileJson,
  Settings,
  Bot,
  GitBranch,
  Package,
  Layers
} from 'lucide-react'

export default function CompleteCodeFuser() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [formData, setFormData] = useState({
    agentName: '',
    description: '',
    inputSchema: '{\n  "type": "object",\n  "properties": {\n    "text": {"type": "string"}\n  }\n}',
    outputSchema: '{\n  "type": "object",\n  "properties": {\n    "result": {"type": "string"}\n  }\n}',
    integrationTarget: 'n8n',
    apiEndpoint: '',
    authMethod: 'hmac',
    secretKey: 's3cr3t'
  })
  
  const [generatedCode, setGeneratedCode] = useState(null)
  const [codeType, setCodeType] = useState('python')
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/agents')
      setAgents(response.data || [])
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const integrationTargets = [
    {
      id: 'n8n',
      name: 'n8n Workflow',
      description: 'Generate n8n workflow JSON',
      icon: GitBranch,
      color: 'bg-orange-100 text-orange-600'
    },
    {
      id: 'python',
      name: 'Python SDK',
      description: 'Generate Python integration code',
      icon: Code,
      color: 'bg-blue-100 text-blue-600'
    },
    {
      id: 'javascript',
      name: 'JavaScript SDK',
      description: 'Generate JS/Node.js integration',
      icon: Package,
      color: 'bg-yellow-100 text-yellow-600'
    },
    {
      id: 'api',
      name: 'REST API',
      description: 'Generate REST API integration',
      icon: Layers,
      color: 'bg-purple-100 text-purple-600'
    }
  ]

  const generateN8nWorkflow = async () => {
    setIsGenerating(true)
    setError(null)
    
    try {
      // Parse schemas
      const inputSchema = JSON.parse(formData.inputSchema)
      const outputSchema = JSON.parse(formData.outputSchema)
      
      // Generate workflow JSON
      const workflow = {
        name: formData.agentName || "GPTGram Agent",
        nodes: [
          {
            id: "webhook",
            type: "n8n-nodes-base.webhook",
            name: "Webhook",
            parameters: {
              httpMethod: "POST",
              path: `gptgram/${(formData.agentName || 'agent').toLowerCase().replace(/\s+/g, '-')}`,
              responseMode: "responseNode",
              options: {}
            },
            typeVersion: 1,
            position: [250, 300]
          },
          {
            id: "validate",
            type: "n8n-nodes-base.code",
            name: "Validate Input",
            parameters: {
              jsCode: `
// Validate input against schema
const schema = ${JSON.stringify(inputSchema, null, 2)};
const input = $input.all()[0].json;

for (const [key, type] of Object.entries(schema)) {
  if (!input.hasOwnProperty(key)) {
    throw new Error(\`Missing required field: \${key}\`);
  }
  const actualType = typeof input[key];
  if (actualType !== type) {
    throw new Error(\`Invalid type for \${key}: expected \${type}, got \${actualType}\`);
  }
}

return { json: input };
`
            },
            typeVersion: 1,
            position: [450, 300]
          },
          {
            id: "gemini",
            type: "n8n-nodes-base.httpRequest",
            name: "Gemini LLM",
            parameters: {
              url: "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
              method: "POST",
              authentication: "genericCredentialType",
              genericAuthType: "httpHeaderAuth",
              sendHeaders: true,
              headerParameters: {
                parameters: [
                  {
                    name: "Content-Type",
                    value: "application/json"
                  }
                ]
              },
              sendQuery: true,
              queryParameters: {
                parameters: [
                  {
                    name: "key",
                    value: "={{ $json.geminiApiKey }}"
                  }
                ]
              },
              sendBody: true,
              bodyParameters: {
                parameters: []
              },
              jsonBody: `{
  "contents": [{
    "parts": [{
      "text": "You are a ${formData.template} agent. Process this input and return ONLY valid JSON matching the output schema. Input: {{ $json }}"
    }]
  }],
  "generationConfig": {
    "temperature": 0,
    "maxOutputTokens": 1024
  }
}`
            },
            typeVersion: 2,
            position: [650, 300]
          },
          {
            id: "parse",
            type: "n8n-nodes-base.code",
            name: "Parse Output",
            parameters: {
              jsCode: `
// Extract and validate output
const response = $input.first().json.candidates[0].content.parts[0].text;
let output;

try {
  // Try to parse JSON from response
  const jsonMatch = response.match(/\{[\\s\\S]*\}/);
  if (jsonMatch) {
    output = JSON.parse(jsonMatch[0]);
  } else {
    throw new Error("No JSON found in response");
  }
} catch (e) {
  throw new Error(\`Failed to parse output: \${e.message}\`);
}

// Validate output schema
const schema = ${JSON.stringify(outputSchema, null, 2)};
for (const [key, type] of Object.entries(schema)) {
  if (!output.hasOwnProperty(key)) {
    throw new Error(\`Missing required output field: \${key}\`);
  }
}

return { json: output };
`
            },
            typeVersion: 1,
            position: [850, 300]
          },
          {
            id: "response",
            type: "n8n-nodes-base.respondToWebhook",
            name: "Respond",
            parameters: {
              respondWith: "json",
              responseBody: "={{ $json }}"
            },
            typeVersion: 1,
            position: [1050, 300]
          }
        ],
        connections: {
          webhook: {
            main: [[{ node: "validate", type: "main", index: 0 }]]
          },
          validate: {
            main: [[{ node: "gemini", type: "main", index: 0 }]]
          },
          gemini: {
            main: [[{ node: "parse", type: "main", index: 0 }]]
          },
          parse: {
            main: [[{ node: "response", type: "main", index: 0 }]]
          }
        },
        settings: {
          executionOrder: "v1"
        },
        staticData: null,
        meta: {
          instanceId: "gptgram_generated"
        },
        tags: ["gptgram", "ai", formData.template]
      }
      
      setGeneratedWorkflow(workflow)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setIsGenerating(false)
    }
  }

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(generatedWorkflow, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const downloadWorkflow = () => {
    const blob = new Blob([JSON.stringify(generatedWorkflow, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${formData.agentName || 'gptgram-agent'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">n8n Code Fuser</h1>
        <p className="text-muted-foreground">
          Generate ready-to-import n8n workflows with Gemini integration
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Configuration */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Agent Configuration</CardTitle>
              <CardDescription>
                Define your agent's behavior and schemas
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Agent Name</label>
                <Input
                  placeholder="My AI Agent"
                  value={formData.agentName}
                  onChange={(e) => setFormData({ ...formData, agentName: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Description</label>
                <Input
                  placeholder="What does this agent do?"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Template</label>
                <select
                  className="w-full px-3 py-2 border rounded-lg"
                  value={formData.template}
                  onChange={(e) => {
                    const template = templates.find(t => t.id === e.target.value)
                    setFormData({
                      ...formData,
                      template: e.target.value,
                      inputSchema: JSON.stringify(template.inputExample, null, 2),
                      outputSchema: JSON.stringify(template.outputExample, null, 2)
                    })
                  }}
                >
                  {templates.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Gemini Model</label>
                <select
                  className="w-full px-3 py-2 border rounded-lg"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                >
                  <option value="gemini-pro">Gemini Pro</option>
                  <option value="gemini-pro-vision">Gemini Pro Vision</option>
                  <option value="gemini-ultra">Gemini Ultra</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium">Input Schema (JSON)</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  rows={5}
                  value={formData.inputSchema}
                  onChange={(e) => setFormData({ ...formData, inputSchema: e.target.value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium">Output Schema (JSON)</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  rows={5}
                  value={formData.outputSchema}
                  onChange={(e) => setFormData({ ...formData, outputSchema: e.target.value })}
                />
              </div>

              <Button
                className="w-full"
                onClick={generateN8nWorkflow}
                disabled={isGenerating}
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Generate n8n Workflow
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Templates */}
          <Card>
            <CardHeader>
              <CardTitle>Templates</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {templates.map(template => (
                  <div
                    key={template.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      formData.template === template.id ? 'border-primary bg-primary/10' : 'hover:border-gray-400'
                    }`}
                    onClick={() => {
                      setFormData({
                        ...formData,
                        template: template.id,
                        inputSchema: JSON.stringify(template.inputExample, null, 2),
                        outputSchema: JSON.stringify(template.outputExample, null, 2)
                      })
                    }}
                  >
                    <p className="font-medium text-sm">{template.name}</p>
                    <p className="text-xs text-muted-foreground">{template.description}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Generated Workflow */}
        <div>
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Generated Workflow
                {generatedWorkflow && (
                  <div className="flex space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={copyToClipboard}
                    >
                      {copied ? (
                        <>
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-1" />
                          Copy
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={downloadWorkflow}
                    >
                      <Download className="h-4 w-4 mr-1" />
                      Download
                    </Button>
                  </div>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
                  <div className="flex items-center space-x-2 text-red-800">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm font-medium">Error</span>
                  </div>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              )}

              {generatedWorkflow ? (
                <div className="space-y-4">
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center space-x-2 text-green-800">
                      <CheckCircle className="h-4 w-4" />
                      <span className="text-sm font-medium">Workflow Generated Successfully</span>
                    </div>
                    <p className="text-sm text-green-700 mt-1">
                      {generatedWorkflow.nodes.length} nodes created
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">Workflow JSON:</p>
                    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-auto max-h-[600px] text-xs">
                      {JSON.stringify(generatedWorkflow, null, 2)}
                    </pre>
                  </div>

                  <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-sm font-medium mb-2">Import Instructions:</p>
                    <ol className="text-sm text-muted-foreground space-y-1">
                      <li>1. Copy or download the JSON above</li>
                      <li>2. Open n8n dashboard</li>
                      <li>3. Click "Import from File" or "Import from URL"</li>
                      <li>4. Paste the JSON or select the file</li>
                      <li>5. Configure Gemini API key in credentials</li>
                      <li>6. Activate and test the workflow</li>
                    </ol>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                  <FileJson className="h-16 w-16 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Configure your agent and click "Generate Workflow"
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
