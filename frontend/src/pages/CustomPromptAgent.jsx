import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { Badge } from '../components/ui/badge'
import {
  Zap,
  Plus,
  Play,
  Eye,
  Trash2,
  Check,
  AlertCircle,
  Code,
  FileText,
  Sparkles
} from 'lucide-react'

export default function CustomPromptAgent() {
  const [agents, setAgents] = useState([])
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [previewMode, setPreviewMode] = useState(false)
  const [examples, setExamples] = useState([])
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    prompt_template: '',
    expected_output_schema: JSON.stringify({
      type: 'object',
      required: ['result'],
      properties: {
        result: { type: 'string' }
      }
    }, null, 2),
    temperature: 0.7,
    max_tokens: 500
  })
  
  // Preview state
  const [previewPrompt, setPreviewPrompt] = useState('')
  const [previewOutputs, setPreviewOutputs] = useState(JSON.stringify({
    Summarizer: {
      summary: 'AI is transforming industries',
      sentences: ['AI is revolutionizing tech', 'Companies are adapting']
    },
    Sentiment: {
      sentiment: 'positive',
      score: 0.85
    }
  }, null, 2))
  const [previewResult, setPreviewResult] = useState(null)

  useEffect(() => {
    loadAgents()
    loadExamples()
  }, [])

  const loadAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/prompt-agent/list')
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to load prompt agents:', error)
    }
  }

  const loadExamples = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/prompt-agent/examples/templates')
      setExamples(response.data.examples || [])
    } catch (error) {
      console.error('Failed to load examples:', error)
    }
  }

  const createAgent = async () => {
    try {
      const schema = JSON.parse(formData.expected_output_schema)
      
      const response = await axios.post('http://localhost:8000/api/prompt-agent/create', {
        name: formData.name,
        description: formData.description,
        prompt_template: formData.prompt_template,
        expected_output_schema: schema,
        temperature: parseFloat(formData.temperature),
        max_tokens: parseInt(formData.max_tokens)
      })
      
      alert('Prompt agent created successfully!')
      setShowCreateForm(false)
      loadAgents()
      
      // Reset form
      setFormData({
        name: '',
        description: '',
        prompt_template: '',
        expected_output_schema: JSON.stringify({
          type: 'object',
          required: ['result'],
          properties: {
            result: { type: 'string' }
          }
        }, null, 2),
        temperature: 0.7,
        max_tokens: 500
      })
    } catch (error) {
      alert('Failed to create agent: ' + error.message)
    }
  }

  const previewResolution = async () => {
    try {
      const outputs = JSON.parse(previewOutputs)
      
      const response = await axios.post('http://localhost:8000/api/prompt-agent/preview', {
        prompt_template: previewPrompt,
        upstream_outputs: outputs
      })
      
      setPreviewResult(response.data)
    } catch (error) {
      alert('Preview failed: ' + error.message)
    }
  }

  const deleteAgent = async (agentId) => {
    if (!confirm('Are you sure you want to delete this agent?')) return
    
    try {
      await axios.delete(`http://localhost:8000/api/prompt-agent/${agentId}`)
      loadAgents()
    } catch (error) {
      alert('Failed to delete agent: ' + error.message)
    }
  }

  const useExample = (example) => {
    setFormData({
      ...formData,
      name: example.name,
      description: example.use_case,
      prompt_template: example.template
    })
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Custom Prompt Agents</h1>
          <p className="text-muted-foreground">
            Create flexible transformation agents using @token prompts
          </p>
        </div>
        <Button onClick={() => setShowCreateForm(!showCreateForm)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Prompt Agent
        </Button>
      </div>

      {/* Token Reference Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center">
            <Code className="h-5 w-5 mr-2" />
            @Token Reference Guide
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold mb-2">Basic Syntax</h4>
              <div className="space-y-1 text-sm">
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">@AgentName</Badge>
                  <span className="text-muted-foreground">Entire agent output</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">@AgentName.field</Badge>
                  <span className="text-muted-foreground">Specific field</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">@AgentName.nested.field</Badge>
                  <span className="text-muted-foreground">Nested fields</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Advanced</h4>
              <div className="space-y-1 text-sm">
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">@AgentName.array[0]</Badge>
                  <span className="text-muted-foreground">Array element</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">@AgentName.items[2].value</Badge>
                  <span className="text-muted-foreground">Complex path</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Preview Tool */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Eye className="h-5 w-5 mr-2" />
            Preview Token Resolution
          </CardTitle>
          <CardDescription>
            Test how your @tokens resolve before creating an agent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Prompt Template (with @tokens)</Label>
            <Textarea
              placeholder='Example: Summarize "@Summarizer.summary" with sentiment @Sentiment.sentiment'
              value={previewPrompt}
              onChange={(e) => setPreviewPrompt(e.target.value)}
              className="font-mono text-sm"
              rows={3}
            />
          </div>
          
          <div>
            <Label>Mock Upstream Outputs (JSON)</Label>
            <Textarea
              value={previewOutputs}
              onChange={(e) => setPreviewOutputs(e.target.value)}
              className="font-mono text-sm"
              rows={8}
            />
          </div>
          
          <Button onClick={previewResolution} variant="outline">
            <Play className="h-4 w-4 mr-2" />
            Preview Resolution
          </Button>
          
          {previewResult && (
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <h4 className="font-semibold mb-2">Resolution Result:</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Tokens Found:</span> {previewResult.tokens_found}
                </div>
                <div>
                  <span className="font-medium">Tokens Resolved:</span> {previewResult.tokens_resolved}
                </div>
                <div>
                  <Label className="text-xs">Resolved Prompt:</Label>
                  <pre className="mt-1 p-2 bg-background rounded border text-xs overflow-x-auto">
                    {previewResult.resolved_prompt}
                  </pre>
                </div>
                {previewResult.unresolved_tokens.length > 0 && (
                  <div>
                    <Label className="text-xs text-red-600">Unresolved Tokens:</Label>
                    {previewResult.unresolved_tokens.map((token, idx) => (
                      <div key={idx} className="mt-1 p-2 bg-red-50 rounded text-xs">
                        <AlertCircle className="h-3 w-3 inline mr-1" />
                        {token.token}: {token.error}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Prompt Agent</CardTitle>
            <CardDescription>
              Define a custom transformation agent using natural language prompts with @token references
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label>Agent Name</Label>
                <Input
                  placeholder="e.g., Content Enricher"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              
              <div>
                <Label>Description</Label>
                <Input
                  placeholder="What does this agent do?"
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                />
              </div>
            </div>
            
            <div>
              <Label>Prompt Template (Use @tokens to reference upstream agents)</Label>
              <Textarea
                placeholder='Example: Create engaging content from "@Summarizer.summary" with @Sentiment.sentiment tone'
                value={formData.prompt_template}
                onChange={(e) => setFormData({...formData, prompt_template: e.target.value})}
                className="font-mono text-sm"
                rows={6}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Use @AgentName.field to reference upstream outputs
              </p>
            </div>
            
            <div>
              <Label>Expected Output Schema (JSON Schema)</Label>
              <Textarea
                value={formData.expected_output_schema}
                onChange={(e) => setFormData({...formData, expected_output_schema: e.target.value})}
                className="font-mono text-sm"
                rows={8}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Temperature (0-1)</Label>
                <Input
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={formData.temperature}
                  onChange={(e) => setFormData({...formData, temperature: e.target.value})}
                />
              </div>
              <div>
                <Label>Max Tokens</Label>
                <Input
                  type="number"
                  min="100"
                  max="2000"
                  value={formData.max_tokens}
                  onChange={(e) => setFormData({...formData, max_tokens: e.target.value})}
                />
              </div>
            </div>
            
            <div className="flex space-x-2">
              <Button onClick={createAgent}>
                <Check className="h-4 w-4 mr-2" />
                Create Agent
              </Button>
              <Button variant="outline" onClick={() => setShowCreateForm(false)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Example Templates */}
      {examples.length > 0 && showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Example Templates</CardTitle>
            <CardDescription>Click to use as starting point</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {examples.map((example, idx) => (
                <div
                  key={idx}
                  onClick={() => useExample(example)}
                  className="p-3 border rounded-lg cursor-pointer hover:bg-muted transition-colors"
                >
                  <div className="flex items-start justify-between mb-1">
                    <h4 className="font-semibold text-sm">{example.name}</h4>
                    <Sparkles className="h-4 w-4 text-purple-500" />
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{example.use_case}</p>
                  <pre className="text-xs bg-background p-2 rounded overflow-x-auto">
                    {example.template.substring(0, 100)}...
                  </pre>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Existing Agents */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Your Prompt Agents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Card key={agent.agent_id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center">
                      <Zap className="h-4 w-4 mr-2 text-purple-500" />
                      {agent.name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {agent.description}
                    </CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteAgent(agent.agent_id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <Label className="text-xs">Prompt Template:</Label>
                    <pre className="mt-1 text-xs bg-muted p-2 rounded overflow-x-auto">
                      {agent.prompt_template.substring(0, 150)}
                      {agent.prompt_template.length > 150 && '...'}
                    </pre>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center space-x-2">
                      <Badge variant="outline">Temp: {agent.temperature}</Badge>
                      <Badge variant="outline">{agent.max_tokens} tokens</Badge>
                    </div>
                    <Badge variant="secondary">{agent.type}</Badge>
                  </div>
                  
                  <Button className="w-full" variant="outline" size="sm">
                    <FileText className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          
          {agents.length === 0 && !showCreateForm && (
            <Card className="col-span-full">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Zap className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="font-semibold text-lg mb-2">No Prompt Agents Yet</h3>
                <p className="text-muted-foreground text-center mb-4">
                  Create your first custom prompt agent to transform data between agents
                </p>
                <Button onClick={() => setShowCreateForm(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Your First Agent
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
