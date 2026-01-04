import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Plus, Trash2, RefreshCw, Check, X, Zap } from 'lucide-react'

export default function AgentManager() {
  const [agents, setAgents] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'n8n',
    endpoint_url: '',
    hmac_secret: '',
    price_cents: 50,
    verification_level: 'L2',
    input_schema: '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}',
    output_schema: '{"type":"object","properties":{"result":{"type":"string"}}}'
  })

  useEffect(() => {
    loadAgents()
  }, [])

  const loadAgents = async () => {
    try {
      setLoading(true)
      const response = await axios.get('http://localhost:8000/api/agents')
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to load agents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    
    try {
      // Parse schemas
      const agentData = {
        ...formData,
        price_cents: parseInt(formData.price_cents),
        input_schema: formData.input_schema ? JSON.parse(formData.input_schema) : null,
        output_schema: formData.output_schema ? JSON.parse(formData.output_schema) : null
      }
      
      const response = await axios.post('http://localhost:8000/api/agents', agentData)
      
      if (response.data.webhook_status === 'tested_ok') {
        alert('✅ Agent created and webhook tested successfully!')
      } else if (response.data.webhook_status === 'test_failed') {
        alert(`⚠️ Agent created but webhook test failed: ${response.data.test_error}\nAgent can still be used, but may not work correctly.`)
      } else {
        alert('✅ Agent created successfully!')
      }
      
      setShowCreateForm(false)
      setFormData({
        name: '',
        description: '',
        type: 'n8n',
        endpoint_url: '',
        hmac_secret: '',
        price_cents: 50,
        verification_level: 'L2',
        input_schema: '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}',
        output_schema: '{"type":"object","properties":{"result":{"type":"string"}}}'
      })
      loadAgents()
    } catch (error) {
      alert(`❌ Failed to create agent: ${error.response?.data?.detail || error.message}`)
    }
  }

  const handleDelete = async (agentId) => {
    if (!confirm('Are you sure you want to delete this agent?')) return
    
    try {
      await axios.delete(`http://localhost:8000/api/agents/${agentId}`)
      alert('✅ Agent deleted')
      loadAgents()
    } catch (error) {
      alert(`❌ Failed to delete agent: ${error.message}`)
    }
  }

  const quickFillN8N = (type) => {
    if (type === 'summarizer') {
      setFormData({
        ...formData,
        name: 'n8n Summarizer',
        description: 'Summarizes long text into key points',
        endpoint_url: 'https://templatechat.app.n8n.cloud/webhook/gptgram/summarize',
        hmac_secret: '',
        input_schema: '{"type":"object","required":["text"],"properties":{"text":{"type":"string"},"maxSentences":{"type":"integer","default":2}}}',
        output_schema: '{"type":"object","properties":{"summary":{"type":"string"},"sentences":{"type":"array"},"key_points":{"type":"array"}}}'
      })
    } else if (type === 'sentiment') {
      setFormData({
        ...formData,
        name: 'Sentiment Analyzer',
        description: 'Analyzes sentiment of text',
        endpoint_url: 'https://templatechat.app.n8n.cloud/webhook/sentiment',
        hmac_secret: '',
        input_schema: '{"type":"object","required":["text"],"properties":{"text":{"type":"string"}}}',
        output_schema: '{"type":"object","properties":{"sentiment":{"type":"string"},"score":{"type":"number"},"confidence":{"type":"number"}}}'
      })
    } else if (type === 'translator') {
      setFormData({
        ...formData,
        name: 'Language Translator',
        description: 'Translates text to target language',
        endpoint_url: 'https://templatechat.app.n8n.cloud/webhook/translation-webhook',
        hmac_secret: '',
        input_schema: '{"type":"object","required":["text","target"],"properties":{"text":{"type":"string"},"target":{"type":"string","default":"es"}}}',
        output_schema: '{"type":"object","properties":{"translated":{"type":"string"},"target":{"type":"string"},"source_language":{"type":"string"}}}'
      })
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Manager</h1>
          <p className="text-muted-foreground">
            Create and manage n8n and custom agents
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={loadAgents} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setShowCreateForm(!showCreateForm)}>
            <Plus className="h-4 w-4 mr-2" />
            Create Agent
          </Button>
        </div>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <Card>
          <CardHeader>
            <CardTitle>Create New Agent</CardTitle>
            <CardDescription>Add a new n8n or custom agent to your library</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              {/* Quick Fill Buttons */}
              <div className="flex gap-2 p-4 bg-blue-50 rounded-lg">
                <span className="text-sm font-medium">Quick Fill:</span>
                <Button type="button" size="sm" variant="outline" onClick={() => quickFillN8N('summarizer')}>
                  Summarizer
                </Button>
                <Button type="button" size="sm" variant="outline" onClick={() => quickFillN8N('sentiment')}>
                  Sentiment
                </Button>
                <Button type="button" size="sm" variant="outline" onClick={() => quickFillN8N('translator')}>
                  Translator
                </Button>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Agent Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="type">Type *</Label>
                  <select
                    id="type"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  >
                    <option value="n8n">n8n</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                <div className="col-span-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>

                <div className="col-span-2">
                  <Label htmlFor="endpoint_url">Webhook URL *</Label>
                  <Input
                    id="endpoint_url"
                    value={formData.endpoint_url}
                    onChange={(e) => setFormData({ ...formData, endpoint_url: e.target.value })}
                    placeholder="https://your-n8n.cloud/webhook/..."
                    required
                  />
                </div>

                <div className="col-span-2">
                  <Label htmlFor="hmac_secret">HMAC Secret (optional)</Label>
                  <Input
                    id="hmac_secret"
                    type="password"
                    value={formData.hmac_secret}
                    onChange={(e) => setFormData({ ...formData, hmac_secret: e.target.value })}
                    placeholder="Leave empty if no HMAC authentication"
                  />
                </div>

                <div>
                  <Label htmlFor="price_cents">Price (cents) *</Label>
                  <Input
                    id="price_cents"
                    type="number"
                    value={formData.price_cents}
                    onChange={(e) => setFormData({ ...formData, price_cents: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="verification_level">Verification Level *</Label>
                  <select
                    id="verification_level"
                    className="w-full px-3 py-2 border rounded-md"
                    value={formData.verification_level}
                    onChange={(e) => setFormData({ ...formData, verification_level: e.target.value })}
                  >
                    <option value="L1">L1 - Basic</option>
                    <option value="L2">L2 - Verified</option>
                    <option value="L3">L3 - Premium</option>
                  </select>
                </div>

                <div className="col-span-2">
                  <Label htmlFor="input_schema">Input Schema (JSON)</Label>
                  <textarea
                    id="input_schema"
                    className="w-full px-3 py-2 border rounded-md font-mono text-sm"
                    rows="3"
                    value={formData.input_schema}
                    onChange={(e) => setFormData({ ...formData, input_schema: e.target.value })}
                  />
                </div>

                <div className="col-span-2">
                  <Label htmlFor="output_schema">Output Schema (JSON)</Label>
                  <textarea
                    id="output_schema"
                    className="w-full px-3 py-2 border rounded-md font-mono text-sm"
                    rows="3"
                    value={formData.output_schema}
                    onChange={(e) => setFormData({ ...formData, output_schema: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex gap-2 justify-end">
                <Button type="button" variant="outline" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  <Check className="h-4 w-4 mr-2" />
                  Create Agent
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Agents List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {loading ? (
          <div className="col-span-full text-center py-8">Loading agents...</div>
        ) : agents.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <Zap className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-gray-600 mb-4">No agents yet. Create your first agent!</p>
            <Button onClick={() => setShowCreateForm(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Agent
            </Button>
          </div>
        ) : (
          agents.map((agent) => (
            <Card key={agent.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{agent.name}</CardTitle>
                    <CardDescription className="mt-1">{agent.description}</CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(agent.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium">{agent.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Price:</span>
                    <span className="font-medium">${(agent.price_cents / 100).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Level:</span>
                    <span className="font-medium">{agent.verification_level}</span>
                  </div>
                  {agent.webhook_status && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Webhook:</span>
                      {agent.webhook_status === 'tested_ok' ? (
                        <span className="flex items-center text-green-600">
                          <Check className="h-4 w-4 mr-1" />
                          Tested OK
                        </span>
                      ) : (
                        <span className="flex items-center text-red-600">
                          <X className="h-4 w-4 mr-1" />
                          Test Failed
                        </span>
                      )}
                    </div>
                  )}
                  <div className="pt-2 border-t">
                    <span className="text-gray-600 text-xs">Endpoint:</span>
                    <p className="text-xs font-mono mt-1 truncate">{agent.endpoint_url}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}
