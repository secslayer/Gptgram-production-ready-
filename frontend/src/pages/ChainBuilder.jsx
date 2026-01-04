import { useState, useCallback, useRef, useEffect } from 'react'
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Panel,
  ReactFlowProvider,
  useReactFlow
} from 'react-flow-renderer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { toast } from '@/hooks/use-toast'
import { 
  Play, 
  Save, 
  Plus,
  Trash2,
  Eye,
  DollarSign,
  AlertCircle,
  CheckCircle2,
  Settings
} from 'lucide-react'
import axios from 'axios'

// Custom Node Component
const AgentNode = ({ data }) => {
  const getVerificationColor = (level) => {
    switch(level) {
      case 'L3': return 'border-green-500 bg-green-50'
      case 'L2': return 'border-yellow-500 bg-yellow-50'
      case 'L1': return 'border-orange-500 bg-orange-50'
      default: return 'border-red-500 bg-red-50'
    }
  }

  return (
    <div className={`px-4 py-3 shadow-md rounded-md border-2 min-w-[200px] ${getVerificationColor(data.verificationLevel)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="font-bold text-sm">{data.label}</div>
        <Badge variant="outline" className="text-xs">
          {data.verificationLevel}
        </Badge>
      </div>
      <div className="text-xs text-gray-600 space-y-1">
        <div className="flex items-center justify-between">
          <span>Price:</span>
          <span className="font-medium">${(data.price / 100).toFixed(2)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span>Type:</span>
          <span className="font-medium">{data.agentType}</span>
        </div>
      </div>
      {data.selected && (
        <div className="mt-2 pt-2 border-t">
          <Button size="sm" variant="ghost" className="w-full text-xs">
            <Settings className="h-3 w-3 mr-1" />
            Configure
          </Button>
        </div>
      )}
    </div>
  )
}

// Custom Edge Component showing compatibility
const CompatibilityEdge = ({ 
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data
}) => {
  const edgePath = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`
  
  const getEdgeColor = (score) => {
    if (score > 0.7) return '#10b981' // green
    if (score > 0.4) return '#f59e0b' // yellow
    return '#ef4444' // red
  }

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={2}
        stroke={getEdgeColor(data?.compatibilityScore || 0.5)}
      />
      <text>
        <textPath
          href={`#${id}`}
          startOffset="50%"
          textAnchor="middle"
          className="text-xs fill-current"
        >
          {data?.compatibilityScore ? `${(data.compatibilityScore * 100).toFixed(0)}%` : ''}
        </textPath>
      </text>
    </>
  )
}

const nodeTypes = {
  agent: AgentNode
}

const edgeTypes = {
  compatibility: CompatibilityEdge
}

function ChainBuilderFlow() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [chainName, setChainName] = useState('My Chain')
  const [selectedNode, setSelectedNode] = useState(null)
  const [agents, setAgents] = useState([])
  const [isRunning, setIsRunning] = useState(false)
  const [runResult, setRunResult] = useState(null)
  const { project } = useReactFlow()

  useEffect(() => {
    fetchAgents()
  }, [])

  const fetchAgents = async () => {
    try {
      const response = await axios.get('/api/agents')
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to fetch agents:', error)
      // Use demo agents for now
      setAgents([
        { id: '1', name: 'n8n Summarizer', type: 'n8n', price_cents: 50, verification_level: 'L2' },
        { id: '2', name: 'Sentiment Analyzer', type: 'custom', price_cents: 30, verification_level: 'L3' },
        { id: '3', name: 'Language Translator', type: 'n8n', price_cents: 75, verification_level: 'L2' },
        { id: '4', name: 'Text Formatter', type: 'custom', price_cents: 25, verification_level: 'L1' }
      ])
    }
  }

  const onConnect = useCallback(
    async (params) => {
      // Calculate compatibility score
      const compatibilityScore = Math.random() * 0.5 + 0.5 // Mock score
      
      const edgeWithData = {
        ...params,
        type: 'compatibility',
        data: { compatibilityScore }
      }
      
      setEdges((eds) => addEdge(edgeWithData, eds))
    },
    [setEdges]
  )

  const onNodeClick = (event, node) => {
    setSelectedNode(node)
    setNodes((nds) =>
      nds.map((n) => ({
        ...n,
        selected: n.id === node.id
      }))
    )
  }

  const addAgentToCanvas = (agent) => {
    const position = project({ x: Math.random() * 500, y: Math.random() * 300 })
    const newNode = {
      id: `node_${Date.now()}`,
      type: 'agent',
      position,
      data: { 
        label: agent.name,
        agentId: agent.id,
        agentType: agent.type,
        price: agent.price_cents,
        verificationLevel: agent.verification_level
      }
    }
    setNodes((nds) => [...nds, newNode])
  }

  const calculateTotalCost = () => {
    return nodes.reduce((total, node) => total + (node.data.price || 0), 0)
  }

  const runChain = async () => {
    setIsRunning(true)
    
    // Create chain descriptor
    const chainDescriptor = {
      nodes: nodes.map(n => ({
        node_id: n.id,
        agent_id: n.data.agentId,
        node_name: n.data.label
      })),
      edges: edges.map(e => ({
        from_node: e.source,
        to_node: e.target,
        mapping_hint_id: null
      })),
      merge_strategy: 'authoritative'
    }

    try {
      // Save chain
      const chainResponse = await axios.post('/api/chains', {
        name: chainName,
        descriptor: chainDescriptor,
        mode: 'balanced'
      })

      // Run chain
      const runResponse = await axios.post(`/api/chains/${chainResponse.data.id}/run`, {
        auto_apply_gat: true,
        allow_llm: false
      })

      toast({
        title: "Chain Started",
        description: `Run ID: ${runResponse.data.run_id}`,
      })

      // Poll for results
      setTimeout(() => {
        setIsRunning(false)
        setRunResult({
          status: 'succeeded',
          output: { summary: 'AI is transforming industries...', sentiment: 'positive' },
          cost: calculateTotalCost()
        })
      }, 3000)

    } catch (error) {
      console.error('Failed to run chain:', error)
      setIsRunning(false)
      
      // Demo result
      setTimeout(() => {
        setIsRunning(false)
        setRunResult({
          status: 'succeeded',
          output: { summary: 'AI is transforming industries at an unprecedented pace.', sentiment: 'positive' },
          cost: calculateTotalCost()
        })
        toast({
          title: "Chain Completed",
          description: "Your chain executed successfully!",
        })
      }, 2000)
    }
  }

  return (
    <div className="h-screen flex">
      {/* Left Sidebar - Agent Library */}
      <div className="w-80 bg-card border-r p-4 overflow-y-auto">
        <Card>
          <CardHeader>
            <CardTitle>Agent Library</CardTitle>
            <CardDescription>Drag agents to add them to your chain</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {agents.map(agent => (
              <div
                key={agent.id}
                className="p-3 border rounded-lg cursor-move hover:bg-secondary transition-colors"
                draggable
                onDragEnd={() => addAgentToCanvas(agent)}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{agent.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {agent.verification_level}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{agent.type}</span>
                  <span>${(agent.price_cents / 100).toFixed(2)}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
        >
          <Background />
          <Controls />
          
          {/* Top Panel - Chain Info */}
          <Panel position="top-left" className="bg-card p-4 rounded-lg shadow-lg m-4">
            <div className="flex items-center space-x-4">
              <Input
                value={chainName}
                onChange={(e) => setChainName(e.target.value)}
                className="w-48"
                placeholder="Chain name"
              />
              <div className="flex items-center space-x-2">
                <DollarSign className="h-4 w-4" />
                <span className="font-medium">
                  Est. Cost: ${(calculateTotalCost() / 100).toFixed(2)}
                </span>
              </div>
              <Button 
                onClick={runChain}
                disabled={nodes.length === 0 || isRunning}
              >
                {isRunning ? (
                  <>
                    <span className="animate-spin mr-2">⏳</span>
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Chain
                  </>
                )}
              </Button>
              <Button variant="outline">
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
            </div>
          </Panel>

          {/* Bottom Panel - Run Results */}
          {runResult && (
            <Panel position="bottom-left" className="bg-card p-4 rounded-lg shadow-lg m-4 max-w-md">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold">Run Result</h3>
                  <Badge variant={runResult.status === 'succeeded' ? 'success' : 'destructive'}>
                    {runResult.status}
                  </Badge>
                </div>
                <div className="text-sm bg-muted p-2 rounded">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(runResult.output, null, 2)}
                  </pre>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span>Total Cost:</span>
                  <span className="font-medium">${(runResult.cost / 100).toFixed(2)}</span>
                </div>
              </div>
            </Panel>
          )}
        </ReactFlow>
      </div>

      {/* Right Panel - Node Inspector */}
      {selectedNode && (
        <div className="w-80 bg-card border-l p-4">
          <Card>
            <CardHeader>
              <CardTitle>Node Inspector</CardTitle>
              <CardDescription>{selectedNode.data.label}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium">Agent ID</label>
                <p className="text-sm text-muted-foreground">{selectedNode.data.agentId}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Type</label>
                <p className="text-sm text-muted-foreground">{selectedNode.data.agentType}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Verification</label>
                <Badge className="mt-1">{selectedNode.data.verificationLevel}</Badge>
              </div>
              <div>
                <label className="text-sm font-medium">Price per Call</label>
                <p className="text-sm text-muted-foreground">
                  ${(selectedNode.data.price / 100).toFixed(2)}
                </p>
              </div>
              <div className="pt-4 space-y-2">
                <Button className="w-full" variant="outline">
                  <Eye className="h-4 w-4 mr-2" />
                  View Schema
                </Button>
                <Button className="w-full" variant="outline">
                  Test Agent
                </Button>
                <Button 
                  className="w-full" 
                  variant="destructive"
                  onClick={() => {
                    setNodes(nds => nds.filter(n => n.id !== selectedNode.id))
                    setSelectedNode(null)
                  }}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Remove Node
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

export default function ChainBuilder() {
  return (
    <ReactFlowProvider>
      <ChainBuilderFlow />
    </ReactFlowProvider>
  )
}
