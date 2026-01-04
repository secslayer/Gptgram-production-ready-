import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import {
  Zap,
  GitBranch,
  AlertCircle,
  CheckCircle,
  Loader2,
  Sparkles,
  Code,
  DollarSign
} from 'lucide-react'

export default function TransformerModal({ 
  isOpen, 
  onClose, 
  sourceNode, 
  targetNode, 
  onAccept 
}) {
  const [activeTab, setActiveTab] = useState('deterministic')
  const [loading, setLoading] = useState(false)
  const [candidates, setCandidates] = useState([])
  const [selectedCandidate, setSelectedCandidate] = useState(null)
  const [geminiCost, setGeminiCost] = useState(0)
  const [error, setError] = useState(null)
  const [template, setTemplate] = useState('')
  const [resolvedPayload, setResolvedPayload] = useState(null)

  useEffect(() => {
    if (isOpen && sourceNode && targetNode) {
      loadTransformOptions()
    }
  }, [isOpen, sourceNode, targetNode])

  const loadTransformOptions = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Try deterministic mappings first
      const deterministicResponse = await axios.post('http://localhost:8000/api/chain/try-deterministic-mappings', {
        source_outputs: [sourceNode.data.outputSchema || {}],
        target_input_schema: targetNode.data.inputSchema || {}
      })
      
      if (deterministicResponse.data.length > 0) {
        setCandidates(deterministicResponse.data)
        setSelectedCandidate(deterministicResponse.data[0])
      }
      
      // Calculate compatibility
      const compatResponse = await axios.post('http://localhost:8000/api/chain/compatibility-score', {
        source_agent_id: sourceNode.id,
        target_agent_id: targetNode.id,
        source_sample_output: sourceNode.data.outputSchema || {}
      })
      
      // Set initial template with @agent tokens
      setTemplate(`Use @${sourceNode.data.label}.text as input for ${targetNode.data.label}`)
      
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const resolveTokens = async () => {
    setLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/chain/resolve-atokens', {
        template: template,
        outputs_map: {
          [sourceNode.data.label]: sourceNode.data.outputSchema || { text: 'sample text' }
        }
      })
      setResolvedPayload(response.data.resolved_payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const runGeminiTransform = async () => {
    if (!window.confirm(`This will cost approximately $${(geminiCost / 100).toFixed(2)}. Continue?`)) {
      return
    }
    
    setLoading(true)
    try {
      // Mock Gemini transform
      const mockPayload = {
        text: sourceNode.data.outputSchema?.text || 'transformed text',
        ...targetNode.data.inputSchema
      }
      
      setSelectedCandidate({
        payload: mockPayload,
        score: 0.92,
        method: 'llm',
        cost_cents: 15,
        tokens: 150
      })
      
      setGeminiCost(15)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleAccept = () => {
    if (selectedCandidate) {
      onAccept({
        method: selectedCandidate.method || activeTab,
        payload: selectedCandidate.payload,
        score: selectedCandidate.score,
        cost: selectedCandidate.cost_cents || 0,
        recipe: selectedCandidate.recipe
      })
      onClose()
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-[800px] max-h-[90vh] overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Insert Transformer</span>
          </CardTitle>
          <CardDescription>
            Transform output from {sourceNode?.data.label} to input for {targetNode?.data.label}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          {/* Tabs */}
          <div className="flex space-x-2 mb-4">
            <Button
              variant={activeTab === 'deterministic' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('deterministic')}
            >
              <GitBranch className="h-4 w-4 mr-1" />
              Deterministic
            </Button>
            <Button
              variant={activeTab === 'gat' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('gat')}
            >
              <Code className="h-4 w-4 mr-1" />
              GAT Suggestions
            </Button>
            <Button
              variant={activeTab === 'gemini' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('gemini')}
            >
              <Sparkles className="h-4 w-4 mr-1" />
              Gemini LLM
            </Button>
          </div>

          {/* Tab Content */}
          <div className="space-y-4">
            {activeTab === 'deterministic' && (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Deterministic Mappings</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {loading ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-6 w-6 animate-spin" />
                      </div>
                    ) : candidates.length > 0 ? (
                      <div className="space-y-2">
                        {candidates.map((candidate, index) => (
                          <div
                            key={index}
                            className={`p-3 border rounded-lg cursor-pointer ${
                              selectedCandidate === candidate ? 'border-primary bg-primary/10' : ''
                            }`}
                            onClick={() => setSelectedCandidate(candidate)}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <Badge variant="outline">
                                Score: {Math.round(candidate.score * 100)}%
                              </Badge>
                              {candidate.method && (
                                <Badge variant="secondary">{candidate.method}</Badge>
                              )}
                            </div>
                            <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                              {JSON.stringify(candidate.payload, null, 2)}
                            </pre>
                            {candidate.recipe && (
                              <div className="mt-2 text-xs text-muted-foreground">
                                Mappings: {candidate.recipe.mappings?.map(m => 
                                  `${m.from} → ${m.to}`
                                ).join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No deterministic mappings found. Try GAT or Gemini.
                      </p>
                    )}
                  </CardContent>
                </Card>

                {/* Template Editor */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Template with @agent tokens</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <textarea
                      className="w-full p-2 border rounded font-mono text-sm"
                      rows={3}
                      value={template}
                      onChange={(e) => setTemplate(e.target.value)}
                      placeholder="Use @Agent.field tokens, e.g., @Summarizer.text"
                    />
                    <div className="mt-2 flex items-center space-x-2">
                      <Button size="sm" onClick={resolveTokens}>
                        Resolve Tokens
                      </Button>
                      {resolvedPayload && (
                        <Badge variant="success">Tokens resolved</Badge>
                      )}
                    </div>
                    {resolvedPayload && (
                      <pre className="mt-2 text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(resolvedPayload, null, 2)}
                      </pre>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {activeTab === 'gat' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">GAT Recommendations</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium">Recipe: sum_to_sent_v1</span>
                        <Badge variant="outline">92% confidence</Badge>
                      </div>
                      <p className="text-xs text-muted-foreground mb-2">
                        Maps summary field to text field with high success rate
                      </p>
                      <div className="text-xs font-mono bg-muted p-2 rounded">
                        summary → text (identity transform)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {activeTab === 'gemini' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Gemini LLM Transform</CardTitle>
                  <CardDescription>Last resort - uses AI to transform data</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <div className="flex items-center space-x-2 text-yellow-800">
                        <AlertCircle className="h-4 w-4" />
                        <span className="text-sm font-medium">Cost Warning</span>
                      </div>
                      <p className="text-sm text-yellow-700 mt-1">
                        This will use Gemini API and incur costs
                      </p>
                      <div className="flex items-center space-x-2 mt-2">
                        <DollarSign className="h-4 w-4" />
                        <span className="font-medium">
                          Estimated cost: ${(geminiCost / 100).toFixed(2)}
                        </span>
                      </div>
                    </div>

                    <div>
                      <p className="text-sm mb-2">Transform Settings:</p>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span>Temperature:</span>
                          <span className="font-mono">0</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Max tokens:</span>
                          <span className="font-mono">512</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Mode:</span>
                          <span className="font-mono">Strict JSON</span>
                        </div>
                      </div>
                    </div>

                    <Button 
                      className="w-full" 
                      onClick={runGeminiTransform}
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <Sparkles className="h-4 w-4 mr-2" />
                          Run Gemini Transform
                        </>
                      )}
                    </Button>

                    {selectedCandidate && selectedCandidate.method === 'llm' && (
                      <div className="p-3 border rounded-lg bg-green-50">
                        <div className="flex items-center space-x-2 text-green-800 mb-2">
                          <CheckCircle className="h-4 w-4" />
                          <span className="text-sm font-medium">Transform Complete</span>
                        </div>
                        <pre className="text-xs bg-white p-2 rounded overflow-auto max-h-32">
                          {JSON.stringify(selectedCandidate.payload, null, 2)}
                        </pre>
                        <div className="mt-2 flex items-center space-x-4 text-xs">
                          <span>Tokens: {selectedCandidate.tokens}</span>
                          <span>Cost: ${(selectedCandidate.cost_cents / 100).toFixed(2)}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center space-x-2 text-red-800">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">{error}</span>
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-2 mt-6">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button 
              onClick={handleAccept}
              disabled={!selectedCandidate}
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Accept Transform
            </Button>
          </div>
        </CardContent>
      </div>
    </div>
  )
}
