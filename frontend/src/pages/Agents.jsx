import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { 
  Bot, 
  Plus, 
  Search,
  CheckCircle2,
  AlertCircle,
  DollarSign,
  Zap,
  Shield
} from 'lucide-react'
import axios from 'axios'
import { toast } from '@/hooks/use-toast'

export default function Agents() {
  const [agents, setAgents] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    setIsLoading(true)
    try {
      const response = await axios.get('/api/agents')
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to fetch agents:', error)
      // Use demo data
      setAgents([
        {
          id: '1',
          name: 'n8n Text Summarizer',
          description: 'Summarizes long text into concise summaries',
          type: 'n8n',
          endpoint_url: 'https://n8n.example.com/webhook/summarize',
          price_cents: 50,
          verification_level: 'L2',
          status: 'active',
          metrics: {
            success_rate: 0.95,
            avg_latency_ms: 1200,
            call_volume: 234
          }
        },
        {
          id: '2',
          name: 'Sentiment Analyzer',
          description: 'Analyzes text sentiment (positive, negative, neutral)',
          type: 'custom',
          endpoint_url: 'https://api.example.com/sentiment',
          price_cents: 30,
          verification_level: 'L3',
          status: 'active',
          metrics: {
            success_rate: 0.98,
            avg_latency_ms: 800,
            call_volume: 456
          }
        },
        {
          id: '3',
          name: 'Language Translator',
          description: 'Translates text between multiple languages',
          type: 'n8n',
          endpoint_url: 'https://n8n.example.com/webhook/translate',
          price_cents: 75,
          verification_level: 'L2',
          status: 'active',
          metrics: {
            success_rate: 0.92,
            avg_latency_ms: 1500,
            call_volume: 123
          }
        },
        {
          id: '4',
          name: 'Content Moderator',
          description: 'Checks content for inappropriate material',
          type: 'custom',
          endpoint_url: 'https://api.example.com/moderate',
          price_cents: 25,
          verification_level: 'L1',
          status: 'pending',
          metrics: {
            success_rate: 0.88,
            avg_latency_ms: 600,
            call_volume: 89
          }
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const verifyAgent = async (agentId) => {
    try {
      const response = await axios.post(`/api/agents/${agentId}/verify`)
      toast({
        title: "Verification Complete",
        description: `Agent verified at level ${response.data.verification_level}`,
      })
      fetchAgents()
    } catch (error) {
      toast({
        title: "Verification Failed",
        description: error.response?.data?.detail || "Could not verify agent",
        variant: "destructive"
      })
    }
  }

  const getVerificationBadge = (level) => {
    switch(level) {
      case 'L3':
        return <Badge className="bg-green-500">L3 Verified</Badge>
      case 'L2':
        return <Badge className="bg-yellow-500">L2 Verified</Badge>
      case 'L1':
        return <Badge className="bg-orange-500">L1 Basic</Badge>
      default:
        return <Badge variant="destructive">Unverified</Badge>
    }
  }

  const getStatusBadge = (status) => {
    switch(status) {
      case 'active':
        return <Badge variant="success">Active</Badge>
      case 'pending':
        return <Badge variant="warning">Pending</Badge>
      default:
        return <Badge variant="secondary">Disabled</Badge>
    }
  }

  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground">
            Manage your A2A-compliant agents and n8n webhooks
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Agent
        </Button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search agents..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Agent Grid */}
      {isLoading ? (
        <div className="text-center py-12">Loading agents...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredAgents.map(agent => (
            <Card key={agent.id} className="hover:shadow-lg transition-shadow cursor-pointer"
                  onClick={() => setSelectedAgent(agent)}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <Bot className="h-8 w-8 text-primary" />
                  <div className="space-x-2">
                    {getVerificationBadge(agent.verification_level)}
                    {getStatusBadge(agent.status)}
                  </div>
                </div>
                <CardTitle className="text-lg">{agent.name}</CardTitle>
                <CardDescription className="line-clamp-2">
                  {agent.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center text-muted-foreground">
                      <DollarSign className="h-3 w-3 mr-1" />
                      Price
                    </span>
                    <span className="font-medium">
                      ${(agent.price_cents / 100).toFixed(2)}/call
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center text-muted-foreground">
                      <Zap className="h-3 w-3 mr-1" />
                      Success Rate
                    </span>
                    <span className="font-medium">
                      {((agent.metrics?.success_rate || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center text-muted-foreground">
                      <Shield className="h-3 w-3 mr-1" />
                      Type
                    </span>
                    <Badge variant="outline" className="text-xs">
                      {agent.type}
                    </Badge>
                  </div>
                </div>
                <div className="mt-4 flex space-x-2">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    className="flex-1"
                    onClick={(e) => {
                      e.stopPropagation()
                      // Test agent
                    }}
                  >
                    Test
                  </Button>
                  {agent.verification_level === 'unverified' && (
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="flex-1"
                      onClick={(e) => {
                        e.stopPropagation()
                        verifyAgent(agent.id)
                      }}
                    >
                      Verify
                    </Button>
                  )}
                  <Button size="sm" className="flex-1">
                    Use
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
             onClick={() => setSelectedAgent(null)}>
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-y-auto" 
                onClick={(e) => e.stopPropagation()}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{selectedAgent.name}</CardTitle>
                  <CardDescription>{selectedAgent.description}</CardDescription>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => setSelectedAgent(null)}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Endpoint</h3>
                <code className="block p-2 bg-muted rounded text-xs">
                  {selectedAgent.endpoint_url}
                </code>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Metrics</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-3 bg-muted rounded">
                    <p className="text-2xl font-bold">
                      {((selectedAgent.metrics?.success_rate || 0) * 100).toFixed(0)}%
                    </p>
                    <p className="text-xs text-muted-foreground">Success Rate</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded">
                    <p className="text-2xl font-bold">
                      {selectedAgent.metrics?.avg_latency_ms || 0}ms
                    </p>
                    <p className="text-xs text-muted-foreground">Avg Latency</p>
                  </div>
                  <div className="text-center p-3 bg-muted rounded">
                    <p className="text-2xl font-bold">
                      {selectedAgent.metrics?.call_volume || 0}
                    </p>
                    <p className="text-xs text-muted-foreground">Total Calls</p>
                  </div>
                </div>
              </div>
              <div className="flex space-x-2">
                <Button className="flex-1">Test Agent</Button>
                <Button variant="outline" className="flex-1">Edit</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
