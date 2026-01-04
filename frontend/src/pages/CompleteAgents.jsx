import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { 
  Bot, 
  Plus, 
  Search, 
  Shield, 
  Zap, 
  Clock,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Play,
  Settings,
  ChevronRight,
  Activity
} from 'lucide-react'
import axios from 'axios'

export default function CompleteAgents() {
  const [agents, setAgents] = useState([
    {
      id: '1',
      name: 'n8n Text Summarizer',
      type: 'n8n',
      description: 'Summarizes long text into concise summaries using n8n workflows',
      endpoint: 'https://templatechat.app.n8n.cloud/webhook/gptgram/summarize',
      verificationLevel: 'L2',
      status: 'active',
      price: 50,
      successRate: 95,
      avgLatency: 1200,
      callVolume: 234,
      owner: 'GPTGram',
      createdAt: '2025-10-15'
    },
    {
      id: '2',
      name: 'Sentiment Analyzer Pro',
      type: 'custom',
      description: 'Advanced sentiment analysis with confidence scoring',
      endpoint: 'https://api.gptgram.ai/sentiment',
      verificationLevel: 'L3',
      status: 'active',
      price: 30,
      successRate: 98,
      avgLatency: 800,
      callVolume: 456,
      owner: 'GPTGram',
      createdAt: '2025-10-12'
    },
    {
      id: '3',
      name: 'n8n Language Translator',
      type: 'n8n',
      description: 'Translates text between 50+ languages using n8n and Google Translate',
      endpoint: 'https://templatechat.app.n8n.cloud/webhook/translation-webhook',
      verificationLevel: 'L2',
      status: 'active',
      price: 75,
      successRate: 92,
      avgLatency: 1500,
      callVolume: 123,
      owner: 'Community',
      createdAt: '2025-10-20'
    },
    {
      id: '4',
      name: 'Content Moderator',
      type: 'custom',
      description: 'AI-powered content moderation for safety',
      endpoint: 'https://api.gptgram.ai/moderate',
      verificationLevel: 'L1',
      status: 'active',
      price: 25,
      successRate: 90,
      avgLatency: 600,
      callVolume: 89,
      owner: 'GPTGram',
      createdAt: '2025-10-25'
    }
  ])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createFormData, setCreateFormData] = useState({
    name: '',
    description: '',
    type: 'custom',
    endpoint_url: '',
    price_cents: 50,
    verification_level: 'L1',
    input_schema: '{}',
    output_schema: '{}',
    example_input: '{}',
    example_output: '{}',
    hmac_secret: ''
  })
  const [testResult, setTestResult] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [filterLevel, setFilterLevel] = useState('all')

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/agents')
      if (response.data) {
        // Merge with mock data for now
        console.log('Fetched agents:', response.data)
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    }
  }

  const getVerificationBadge = (level) => {
    const badges = {
      'L1': { label: 'L1', variant: 'secondary', icon: Shield, color: 'text-gray-500' },
      'L2': { label: 'L2', variant: 'default', icon: Shield, color: 'text-blue-500' },
      'L3': { label: 'L3', variant: 'success', icon: CheckCircle, color: 'text-green-500' },
      'UNVERIFIED': { label: 'Unverified', variant: 'outline', icon: AlertCircle, color: 'text-yellow-500' }
    }
    return badges[level] || badges['UNVERIFIED']
  }

  const AgentCard = ({ agent }) => {
    const verification = getVerificationBadge(agent.verificationLevel)
    
    return (
      <Card className="hover:shadow-lg transition-all cursor-pointer" onClick={() => setSelectedAgent(agent)}>
        <CardHeader>
          <div className="flex justify-between items-start">
            <div className="flex items-start space-x-3">
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                agent.type === 'n8n' ? 'bg-orange-100' : 'bg-blue-100'
              }`}>
                <Bot className={`h-5 w-5 ${
                  agent.type === 'n8n' ? 'text-orange-600' : 'text-blue-600'
                }`} />
              </div>
              <div>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <span>{agent.name}</span>
                  {agent.type === 'n8n' && (
                    <Badge variant="outline" className="ml-2">n8n</Badge>
                  )}
                </CardTitle>
                <CardDescription className="mt-1">
                  {agent.description}
                </CardDescription>
              </div>
            </div>
            <Badge variant={verification.variant} className="flex items-center space-x-1">
              <verification.icon className="h-3 w-3" />
              <span>{verification.label}</span>
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div>
              <p className="text-sm text-muted-foreground">Success Rate</p>
              <div className="flex items-center space-x-1">
                <Activity className="h-4 w-4 text-green-500" />
                <span className="font-semibold">{agent.successRate}%</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Latency</p>
              <div className="flex items-center space-x-1">
                <Clock className="h-4 w-4 text-blue-500" />
                <span className="font-semibold">{agent.avgLatency}ms</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Call Volume</p>
              <div className="flex items-center space-x-1">
                <Zap className="h-4 w-4 text-purple-500" />
                <span className="font-semibold">{agent.callVolume}</span>
              </div>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Price</p>
              <span className="font-semibold text-lg">${(agent.price / 100).toFixed(2)}</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between pt-4 border-t">
            <span className="text-sm text-muted-foreground">
              by {agent.owner} • Created {agent.createdAt}
            </span>
            <div className="flex space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={async () => {
                  try {
                    await axios.post(`http://localhost:8000/api/agents/verify/${agent.id}`)
                    alert('Agent verified successfully!')
                    loadAgents()
                  } catch (error) {
                    alert('Verification failed: ' + error.message)
                  }
                }}
              >
                <CheckCircle className="h-4 w-4 mr-2" />
                Verify
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => {
                  localStorage.setItem('selectedAgent', JSON.stringify(agent))
                  window.location.href = '/chains'
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add to Chain
              </Button>
              <Button size="sm">
                Use
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.description.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = filterLevel === 'all' || agent.verificationLevel === filterLevel
    return matchesSearch && matchesFilter
  })

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agent Marketplace</h1>
          <p className="text-muted-foreground">
            Discover and deploy A2A-compliant agents with automatic verification
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} variant="default" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search agents by name or description..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex space-x-2">
              <Button
                variant={filterLevel === 'all' ? 'default' : 'outline'}
                onClick={() => setFilterLevel('all')}
              >
                All
              </Button>
              <Button
                variant={filterLevel === 'L1' ? 'default' : 'outline'}
                onClick={() => setFilterLevel('L1')}
              >
                L1
              </Button>
              <Button
                variant={filterLevel === 'L2' ? 'default' : 'outline'}
                onClick={() => setFilterLevel('L2')}
              >
                L2
              </Button>
              <Button
                variant={filterLevel === 'L3' ? 'default' : 'outline'}
                onClick={() => setFilterLevel('L3')}
              >
                L3
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Agents</p>
                <p className="text-2xl font-bold">{agents.length}</p>
              </div>
              <Bot className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">L3 Verified</p>
                <p className="text-2xl font-bold">{agents.filter(a => a.verificationLevel === 'L3').length}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">n8n Agents</p>
                <p className="text-2xl font-bold">{agents.filter(a => a.type === 'n8n').length}</p>
              </div>
              <Zap className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Success</p>
                <p className="text-2xl font-bold">
                  {Math.round(agents.reduce((acc, a) => acc + a.successRate, 0) / agents.length)}%
                </p>
              </div>
              <Activity className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Agent Grid */}
      <div className="space-y-4">
        {filteredAgents.length > 0 ? (
          filteredAgents.map(agent => (
            <AgentCard key={agent.id} agent={agent} />
          ))
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <Bot className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                No agents found matching your criteria
              </p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setSelectedAgent(null)}>
          <Card className="w-[600px] max-h-[80vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <CardHeader>
              <CardTitle>{selectedAgent.name}</CardTitle>
              <CardDescription>{selectedAgent.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h4 className="font-semibold mb-2">Endpoint</h4>
                  <div className="flex items-center space-x-2">
                    <code className="flex-1 p-2 bg-muted rounded text-sm">{selectedAgent.endpoint}</code>
                    <Button size="sm" variant="outline">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Performance Metrics</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="p-3 bg-muted rounded">
                      <p className="text-sm text-muted-foreground">Success Rate</p>
                      <p className="text-lg font-semibold">{selectedAgent.successRate}%</p>
                    </div>
                    <div className="p-3 bg-muted rounded">
                      <p className="text-sm text-muted-foreground">Avg Latency</p>
                      <p className="text-lg font-semibold">{selectedAgent.avgLatency}ms</p>
                    </div>
                    <div className="p-3 bg-muted rounded">
                      <p className="text-sm text-muted-foreground">Total Calls</p>
                      <p className="text-lg font-semibold">{selectedAgent.callVolume}</p>
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-end space-x-2 pt-4">
                  <Button variant="outline" onClick={() => setSelectedAgent(null)}>
                    Close
                  </Button>
                  <Button>
                    Add to Chain
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Create Agent Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-[600px] max-h-[80vh] overflow-y-auto">
            <CardHeader>
              <CardTitle>Create New Agent</CardTitle>
              <CardDescription>
                Define your agent's schema and webhook configuration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Name</label>
                  <Input
                    value={createFormData.name}
                    onChange={(e) => setCreateFormData({...createFormData, name: e.target.value})}
                    placeholder="Agent name"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Type</label>
                  <select
                    className="w-full px-3 py-2 border rounded-lg"
                    value={createFormData.type}
                    onChange={(e) => setCreateFormData({...createFormData, type: e.target.value})}
                  >
                    <option value="custom">Custom</option>
                    <option value="n8n">n8n Webhook</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <Input
                  value={createFormData.description}
                  onChange={(e) => setCreateFormData({...createFormData, description: e.target.value})}
                  placeholder="What does this agent do?"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Webhook URL</label>
                <Input
                  value={createFormData.endpoint_url}
                  onChange={(e) => setCreateFormData({...createFormData, endpoint_url: e.target.value})}
                  placeholder="https://..."
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Price (cents)</label>
                  <Input
                    type="number"
                    value={createFormData.price_cents}
                    onChange={(e) => setCreateFormData({...createFormData, price_cents: parseInt(e.target.value)})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Verification Level</label>
                  <select
                    className="w-full px-3 py-2 border rounded-lg"
                    value={createFormData.verification_level}
                    onChange={(e) => setCreateFormData({...createFormData, verification_level: e.target.value})}
                  >
                    <option value="L1">L1 - Self Declared</option>
                    <option value="L2">L2 - Auto Verified</option>
                    <option value="L3">L3 - Manually Reviewed</option>
                  </select>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Input Schema (JSON)</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  rows={3}
                  value={createFormData.input_schema}
                  onChange={(e) => setCreateFormData({...createFormData, input_schema: e.target.value})}
                  placeholder='{"text": "string", "maxSentences": "number"}'
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Output Schema (JSON)</label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg font-mono text-sm"
                  rows={3}
                  value={createFormData.output_schema}
                  onChange={(e) => setCreateFormData({...createFormData, output_schema: e.target.value})}
                  placeholder='{"summary": "string"}'
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">HMAC Secret</label>
                <Input
                  type="password"
                  value={createFormData.hmac_secret}
                  onChange={(e) => setCreateFormData({...createFormData, hmac_secret: e.target.value})}
                  placeholder="Secret for webhook signing"
                />
              </div>
              
              {/* Test Result */}
              {testResult && (
                <div className={`p-3 rounded ${testResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                  {testResult.success ? '✓ Webhook test successful' : `✗ ${testResult.error}`}
                </div>
              )}
              
              <div className="flex justify-end space-x-2 pt-4">
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false)
                    setTestResult(null)
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={async () => {
                    try {
                      const response = await axios.post(createFormData.endpoint_url, 
                        JSON.parse(createFormData.example_input || '{}'),
                        { timeout: 5000 }
                      )
                      setTestResult({ success: true })
                    } catch (error) {
                      setTestResult({ success: false, error: error.message })
                    }
                  }}
                >
                  Test Webhook
                </Button>
                <Button
                  onClick={async () => {
                    setIsCreating(true)
                    try {
                      await axios.post('http://localhost:8000/api/agents', createFormData, {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                      })
                      setShowCreateModal(false)
                      fetchAgents() // Refresh list
                    } catch (error) {
                      console.error('Failed to create agent:', error)
                    } finally {
                      setIsCreating(false)
                    }
                  }}
                  disabled={isCreating || !createFormData.name || !createFormData.endpoint_url}
                >
                  {isCreating ? 'Creating...' : 'Create Agent'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
