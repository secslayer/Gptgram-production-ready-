import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'
import ReactFlow, {
  ReactFlowProvider,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Position,
  Handle,
  ConnectionMode,
  useReactFlow
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import TransformerModal from '../components/TransformerModal'
import {
  Bot,
  GitBranch,
  Play,
  Save,
  Plus,
  Settings,
  DollarSign,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Loader2,
  Search,
  Shield,
  Zap,
  Code,
  Sparkles
} from 'lucide-react'

// Custom Agent Node Component
const AgentNode = ({ data, isConnectable }) => {
  const getVerificationColor = (level) => {
    switch (level) {
      case 'L3': return 'border-green-500 bg-green-50'
      case 'L2': return 'border-blue-500 bg-blue-50'
      case 'L1': return 'border-gray-500 bg-gray-50'
      case 'TRANSFORMER': return 'border-purple-500 bg-purple-50'
      default: return 'border-yellow-500 bg-yellow-50'
    }
  }

  const getTransformBadge = (method) => {
    switch (method) {
      case 'deterministic':
        return { color: 'bg-green-100 text-green-800', icon: <GitBranch className="h-3 w-3" /> }
      case 'gat':
        return { color: 'bg-blue-100 text-blue-800', icon: <Code className="h-3 w-3" /> }
      case 'llm':
        return { color: 'bg-purple-100 text-purple-800', icon: <Sparkles className="h-3 w-3" /> }
      default:
        return null
    }
  }

  return (
    <div className={`px-4 py-3 shadow-lg rounded-lg border-2 ${getVerificationColor(data.verificationLevel)} min-w-[200px] max-w-[250px]`}>
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        style={{ background: '#555', width: 12, height: 12, left: -6 }}
      />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          {data.isTransformer ? (
            <Zap className="h-5 w-5 text-purple-600" />
          ) : (
            <Bot className="h-5 w-5" />
          )}
          <span className="font-semibold text-sm">{data.label}</span>
        </div>
        <Badge variant="outline" className="text-xs">
          {data.verificationLevel}
        </Badge>
      </div>
      
      {data.description && (
        <p className="text-xs text-gray-600 mb-2">{data.description}</p>
      )}
      
      {data.transformMethod && (
        <div className="mb-2">
          <Badge className={`text-xs ${getTransformBadge(data.transformMethod)?.color}`}>
            <span className="flex items-center gap-1">
              {getTransformBadge(data.transformMethod)?.icon}
              {data.transformMethod}
            </span>
          </Badge>
        </div>
      )}
      
      <div className="flex items-center justify-between text-xs">
        <span className="text-gray-500">${(data.price / 100).toFixed(2)}</span>
        {data.type === 'n8n' && (
          <Badge variant="secondary" className="text-xs">n8n</Badge>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Right}
        isConnectable={isConnectable}
        style={{ background: '#555', width: 12, height: 12, right: -6 }}
      />
    </div>
  )
}

const nodeTypes = {
  agentNode: AgentNode
}

// Custom edge with transform method label
const CustomEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data
}) => {
  const edgePath = `M ${sourceX},${sourceY} L ${targetX},${targetY}`
  const midX = (sourceX + targetX) / 2
  const midY = (sourceY + targetY) / 2

  const getEdgeColor = (score) => {
    if (score >= 0.7) return '#22c55e'
    if (score >= 0.4) return '#eab308'
    return '#ef4444'
  }

  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={2}
        stroke={getEdgeColor(data?.score || 0.5)}
        fill="none"
        markerEnd="url(#arrowhead)"
      />
      {data?.transformMethod && (
        <foreignObject x={midX - 40} y={midY - 10} width={80} height={20}>
          <Badge className="text-xs">
            {data.transformMethod}
          </Badge>
        </foreignObject>
      )}
      {data?.score && (
        <text x={midX} y={midY + 20} fontSize={12} fontWeight={600} textAnchor="middle">
          {Math.round(data.score * 100)}%
        </text>
      )}
    </>
  )
}

const edgeTypes = {
  custom: CustomEdge
}

function ChainBuilderFlow() {
  const reactFlowInstance = useReactFlow()
  const [showTransformerModal, setShowTransformerModal] = useState(false)
  const [transformerSource, setTransformerSource] = useState(null)
  const [transformerTarget, setTransformerTarget] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [executionStep, setExecutionStep] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [chainName, setChainName] = useState('My Chain')
  const [chainData, setChainData] = useState({ nodes: [], edges: [], dag: {} })
  
  const [nodes, setNodes, onNodesChange] = useNodesState([
    {
      id: 'input',
      type: 'agentNode',
      position: { x: 100, y: 200 },
      data: {
        label: 'Input',
        description: 'Chain input',
        verificationLevel: 'SYSTEM',
        price: 0,
        type: 'system',
        outputSchema: { text: { type: 'string' } }
      }
    }
  ])
  
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  const availableAgents = [
    {
      id: 'summarizer',
      name: 'n8n Summarizer',
      type: 'n8n',
      description: 'Summarizes text using AI',
      verificationLevel: 'L2',
      price: 50,
      inputSchema: { 
        type: 'object',
        required: ['text'],
        properties: {
          text: { type: 'string' },
          maxSentences: { type: 'number', default: 2 }
        }
      },
      outputSchema: { 
        type: 'object',
        properties: {
          summary: { type: 'string' }
        }
      }
    },
    {
      id: 'sentiment',
      name: 'Sentiment Analyzer',
      type: 'custom',
      description: 'Analyzes text sentiment',
      verificationLevel: 'L3',
      price: 30,
      inputSchema: { 
        type: 'object',
        required: ['text'],
        properties: {
          text: { type: 'string' }
        }
      },
      outputSchema: { 
        type: 'object',
        properties: {
          sentiment: { type: 'string', enum: ['positive', 'negative', 'neutral'] },
          score: { type: 'number', minimum: 0, maximum: 1 }
        }
      }
    },
    {
      id: 'translator',
      name: 'n8n Translator',
      type: 'n8n',
      description: 'Translates text to target language',
      verificationLevel: 'L2',
      price: 75,
      inputSchema: { 
        type: 'object',
        required: ['text', 'target'],
        properties: {
          text: { type: 'string' },
          target: { type: 'string', enum: ['es', 'fr', 'de', 'it', 'pt'] }
        }
      },
      outputSchema: { 
        type: 'object',
        properties: {
          translated: { type: 'string' },
          target: { type: 'string' }
        }
      }
    }
  ]

  const onConnect = useCallback(async (params) => {
    const sourceNode = nodes.find(n => n.id === params.source)
    const targetNode = nodes.find(n => n.id === params.target)
    
    try {
      // Calculate compatibility
      const response = await axios.post('http://localhost:8000/api/chain/compatibility-score', {
        source_agent_id: sourceNode?.id,
        target_agent_id: targetNode?.id,
        source_sample_output: sourceNode?.data.outputSchema || {}
      })
      
      const compatibilityScore = response.data.score
      
      // If score is low, offer transformer
      if (compatibilityScore < 0.7 && !sourceNode?.data.isTransformer) {
        setTransformerSource(sourceNode)
        setTransformerTarget(targetNode)
        setShowTransformerModal(true)
        return
      }
      
      // Create edge with compatibility info
      const newEdge = {
        ...params,
        id: `${params.source}-${params.target}`,
        type: 'custom',
        animated: true,
        data: { 
          score: compatibilityScore,
          transformMethod: sourceNode?.data.transformMethod
        }
      }
      
      setEdges((eds) => addEdge(newEdge, eds))
      
      // Update DAG
      setChainData(prev => ({
        ...prev,
        edges: [...prev.edges, { from: params.source, to: params.target, score: compatibilityScore }]
      }))
      
    } catch (error) {
      console.error('Failed to check compatibility:', error)
    }
  }, [nodes, setEdges])

  const handleTransformerAccept = (transformData) => {
    // Create transformer node
    const transformerId = `transformer-${Date.now()}`
    const transformerNode = {
      id: transformerId,
      type: 'agentNode',
      position: {
        x: (transformerSource.position.x + transformerTarget.position.x) / 2,
        y: (transformerSource.position.y + transformerTarget.position.y) / 2
      },
      data: {
        label: 'Transformer',
        description: `${transformData.method} transform`,
        verificationLevel: 'TRANSFORMER',
        price: transformData.cost || 0,
        isTransformer: true,
        transformMethod: transformData.method,
        transformPayload: transformData.payload,
        inputSchema: transformerSource?.data.outputSchema,
        outputSchema: transformData.payload
      }
    }
    
    setNodes(nds => [...nds, transformerNode])
    
    // Create edges
    const edge1 = {
      id: `${transformerSource.id}-${transformerId}`,
      source: transformerSource.id,
      target: transformerId,
      type: 'custom',
      animated: true,
      data: { score: 1.0, transformMethod: 'input' }
    }
    
    const edge2 = {
      id: `${transformerId}-${transformerTarget.id}`,
      source: transformerId,
      target: transformerTarget.id,
      type: 'custom',
      animated: true,
      data: { score: transformData.score, transformMethod: transformData.method }
    }
    
    setEdges(eds => [...eds, edge1, edge2])
    
    // Update DAG
    setChainData(prev => ({
      ...prev,
      nodes: [...prev.nodes, { id: transformerId, type: 'transformer', method: transformData.method }],
      edges: [
        ...prev.edges,
        { from: transformerSource.id, to: transformerId, score: 1.0 },
        { from: transformerId, to: transformerTarget.id, score: transformData.score }
      ]
    }))
  }

  const addAgentToCanvas = (agent) => {
    const newNode = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position: { 
        x: Math.random() * 400 + 200, 
        y: Math.random() * 300 + 100 
      },
      data: {
        label: agent.name,
        description: agent.description,
        verificationLevel: agent.verificationLevel,
        price: agent.price,
        type: agent.type,
        inputSchema: agent.inputSchema,
        outputSchema: agent.outputSchema,
        agentId: agent.id
      }
    }
    setNodes((nds) => nds.concat(newNode))
    
    // Update chain data
    setChainData(prev => ({
      ...prev,
      nodes: [...prev.nodes, { id: newNode.id, agentId: agent.id, type: 'agent' }]
    }))
  }

  const calculateTotalCost = () => {
    return nodes.reduce((sum, node) => sum + (node.data.price || 0), 0)
  }

  const runChain = async () => {
    setIsRunning(true)
    setExecutionStep(0)
    
    try {
      // Get topological order
      const dagOrder = getTopologicalOrder()
      
      // Execute chain
      const response = await axios.post('http://localhost:8000/api/chain/execute', {
        chain_id: `chain-${Date.now()}`,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.data.isTransformer ? 'transformer' : 'agent',
          agent_id: n.data.agentId,
          transform_method: n.data.transformMethod,
          input_schema: n.data.inputSchema,
          output_schema: n.data.outputSchema
        })),
        edges: edges.map(e => ({
          source: e.source,
          target: e.target,
          score: e.data?.score
        })),
        execution_order: dagOrder
      })
      
      // Update wallet balance
      await updateWalletBalance(calculateTotalCost())
      
      // Save run to analytics
      await saveRunToAnalytics(response.data)
      
    } catch (error) {
      console.error('Chain execution failed:', error)
    } finally {
      setIsRunning(false)
      setExecutionStep(0)
    }
  }

  const getTopologicalOrder = () => {
    const visited = new Set()
    const order = []
    const adjList = {}
    
    // Build adjacency list
    edges.forEach(edge => {
      if (!adjList[edge.source]) adjList[edge.source] = []
      adjList[edge.source].push(edge.target)
    })
    
    // DFS topological sort
    const dfs = (nodeId) => {
      if (visited.has(nodeId)) return
      visited.add(nodeId)
      
      if (adjList[nodeId]) {
        adjList[nodeId].forEach(child => dfs(child))
      }
      
      order.unshift(nodeId)
    }
    
    nodes.forEach(node => {
      if (!visited.has(node.id)) {
        dfs(node.id)
      }
    })
    
    return order
  }

  const updateWalletBalance = async (cost) => {
    await axios.post('http://localhost:8000/api/wallet/deduct', {
      amount_cents: cost
    }, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    })
  }

  const saveRunToAnalytics = async (runData) => {
    await axios.post('http://localhost:8000/api/analytics/save-run', {
      ...runData,
      chain_name: chainName,
      total_cost: calculateTotalCost(),
      timestamp: new Date().toISOString()
    })
  }

  const saveChain = async () => {
    const chainDescriptor = {
      name: chainName,
      nodes: nodes.map(n => ({
        node_id: n.id,
        agent_name: n.data.label,
        agent_id: n.data.agentId,
        verification_level: n.data.verificationLevel,
        price: n.data.price,
        is_transformer: n.data.isTransformer,
        transform_method: n.data.transformMethod
      })),
      edges: edges.map(e => ({
        from_node: e.source,
        to_node: e.target,
        compatibility_score: e.data?.score || 0.85,
        transform_method: e.data?.transformMethod
      })),
      dag_order: getTopologicalOrder(),
      total_cost: calculateTotalCost()
    }
    
    try {
      await axios.post('http://localhost:8000/api/chain/save', chainDescriptor)
      alert('Chain saved successfully!')
    } catch (error) {
      console.error('Failed to save chain:', error)
    }
  }

  // Load recommendations
  useEffect(() => {
    if (selectedNode && selectedNode.id !== 'input') {
      loadRecommendations()
    }
  }, [selectedNode])
  
  const loadRecommendations = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/chain/recommend-agents', {
        params: {
          context_node_ids: [selectedNode?.id],
          top_k: 5
        }
      })
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    }
  }

  const filteredAgents = availableAgents.filter(agent =>
    agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    agent.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="h-screen flex">
      {/* Left Sidebar - Agent Library */}
      <div className="w-80 border-r bg-background p-4 overflow-y-auto">
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-2">Agent Library</h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            {filteredAgents.map(agent => (
              <Card 
                key={agent.id}
                className="cursor-pointer hover:shadow-md transition-all"
                onClick={() => addAgentToCanvas(agent)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between mb-1">
                    <div className="flex items-center space-x-2">
                      <Bot className="h-4 w-4" />
                      <span className="font-medium text-sm">{agent.name}</span>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {agent.verificationLevel}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">{agent.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      ${(agent.price / 100).toFixed(2)}
                    </span>
                    {agent.type === 'n8n' && (
                      <Badge variant="secondary" className="text-xs">n8n</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="border-b p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Input
                value={chainName}
                onChange={(e) => setChainName(e.target.value)}
                className="text-lg font-semibold w-64"
              />
              <Badge variant="outline">
                {nodes.length} nodes
              </Badge>
              <div className="flex items-center space-x-2">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className="font-semibold">
                  ${(calculateTotalCost() / 100).toFixed(2)}
                </span>
                <span className="text-sm text-muted-foreground">per run</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button variant="outline" onClick={saveChain}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
              <Button onClick={runChain} disabled={isRunning || nodes.length < 2}>
                {isRunning ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Run Chain
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(event, node) => setSelectedNode(node)}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            connectionMode={ConnectionMode.Loose}
            defaultViewport={{ x: 0, y: 0, zoom: 1 }}
            fitView
          >
            <Background variant="dots" gap={12} size={1} />
            <Controls />
            <MiniMap />
            <svg>
              <defs>
                <marker
                  id="arrowhead"
                  markerWidth="10"
                  markerHeight="10"
                  refX="9"
                  refY="5"
                  orient="auto"
                >
                  <polygon points="0 0, 10 5, 0 10" fill="#555" />
                </marker>
              </defs>
            </svg>
          </ReactFlow>
          
          {/* Legend */}
          <Card className="absolute bottom-4 left-4 w-64">
            <CardContent className="p-3">
              <h4 className="font-medium text-sm mb-2">Compatibility & Transform</h4>
              <div className="space-y-1 text-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded" />
                  <span>High compatibility (&gt;70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded" />
                  <span>Medium (40-70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded" />
                  <span>Low (&lt;40%)</span>
                </div>
                <div className="flex items-center space-x-2 mt-2">
                  <Badge className="text-xs bg-green-100 text-green-800">deterministic</Badge>
                  <span>Rule-based</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className="text-xs bg-blue-100 text-blue-800">gat</Badge>
                  <span>ML patterns</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className="text-xs bg-purple-100 text-purple-800">llm</Badge>
                  <span>AI transform</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Recommendations Panel */}
      {recommendations.length > 0 && selectedNode && (
        <div className="absolute bottom-20 right-4 w-80 z-10">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Recommended Next Agents</CardTitle>
              <CardDescription>Based on compatibility analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recommendations.map(rec => (
                  <div
                    key={rec.agent_id}
                    className="p-2 border rounded-lg hover:bg-muted cursor-pointer"
                    onClick={() => {
                      const agent = availableAgents.find(a => a.id === rec.agent_id)
                      if (agent) addAgentToCanvas(agent)
                    }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium">{rec.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {Math.round(rec.compatibility_score * 100)}%
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {rec.reasons[0]}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      {/* Transformer Modal */}
      <TransformerModal
        isOpen={showTransformerModal}
        onClose={() => {
          setShowTransformerModal(false)
          setTransformerSource(null)
          setTransformerTarget(null)
        }}
        sourceNode={transformerSource}
        targetNode={transformerTarget}
        onAccept={handleTransformerAccept}
      />
    </div>
  )
}

export default function FixedChainBuilder() {
  return (
    <ReactFlowProvider>
      <ChainBuilderFlow />
    </ReactFlowProvider>
  )
}
