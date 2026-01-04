import { useState, useCallback, useEffect, useRef } from 'react'
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  MiniMap,
  Controls,
  Background,
  Handle,
  Position,
  MarkerType,
  useReactFlow
} from 'reactflow'
import 'reactflow/dist/style.css'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import {
  Search,
  Play,
  Save,
  Plus,
  Zap,
  Bot,
  Copy,
  Trash,
  Edit,
  Check,
  AlertCircle,
  DollarSign,
  Activity
} from 'lucide-react'

// ============= CUSTOM NODE TYPES =============

const AgentNode = ({ data, isConnectable }) => {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div 
      className={`px-4 py-3 shadow-lg rounded-lg border-2 bg-white ${
        data.verification_level === 'L3' ? 'border-green-500' :
        data.verification_level === 'L2' ? 'border-blue-500' :
        'border-gray-300'
      }`}
      onDoubleClick={() => setShowDetails(!showDetails)}
      style={{ minWidth: '200px' }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-blue-500"
        isConnectable={isConnectable}
      />
      
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Bot className="h-4 w-4 text-blue-600" />
          <div className="font-semibold">{data.name || 'Agent'}</div>
        </div>
        <Badge variant={data.type === 'n8n' ? 'secondary' : 'default'} className="text-xs">
          {data.type || 'custom'}
        </Badge>
      </div>
      
      <div className="mt-2 text-xs text-gray-600">
        {data.description || 'No description'}
      </div>
      
      <div className="mt-2 flex items-center justify-between text-xs">
        <Badge variant="outline" className="text-xs">
          {data.verification_level || 'L1'}
        </Badge>
        <div className="flex items-center space-x-1">
          <DollarSign className="h-3 w-3" />
          <span>{data.price_cents ? `${data.price_cents}¢` : 'Free'}</span>
        </div>
      </div>
      
      {showDetails && (
        <div className="mt-3 pt-3 border-t text-xs">
          <div><strong>Input:</strong> {JSON.stringify(data.input_schema?.required || [])}</div>
          <div><strong>Output:</strong> {JSON.stringify(data.output_schema?.properties ? Object.keys(data.output_schema.properties) : [])}</div>
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-500"
        isConnectable={isConnectable}
      />
    </div>
  )
}

const ModeratorNode = ({ data, isConnectable, id }) => {
  const [editing, setEditing] = useState(false)
  const [prompt, setPrompt] = useState(data.prompt_template || '')
  const [showTokenGuide, setShowTokenGuide] = useState(false)
  
  const handleSave = async () => {
    try {
      await axios.put(`http://localhost:8000/api/moderator/node/${id}`, {
        prompt_template: prompt
      })
      data.prompt_template = prompt
      setEditing(false)
    } catch (error) {
      console.error('Failed to update moderator:', error)
    }
  }
  
  return (
    <div 
      className="px-4 py-3 shadow-lg rounded-lg border-2 border-purple-500 bg-purple-50"
      style={{ minWidth: '250px', maxWidth: '350px' }}
      onDoubleClick={() => setEditing(true)}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-purple-500"
        style={{ left: '30%' }}
        id="input-1"
        isConnectable={isConnectable}
      />
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-purple-500"
        style={{ left: '70%' }}
        id="input-2"
        isConnectable={isConnectable}
      />
      
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Zap className="h-4 w-4 text-purple-600" />
          <div className="font-semibold">Moderator Agent</div>
        </div>
        <div className="flex space-x-1">
          {editing && (
            <Button size="sm" variant="ghost" onClick={handleSave}>
              <Check className="h-3 w-3" />
            </Button>
          )}
          <Button size="sm" variant="ghost" onClick={() => setShowTokenGuide(!showTokenGuide)}>
            <AlertCircle className="h-3 w-3" />
          </Button>
        </div>
      </div>
      
      {editing ? (
        <div className="space-y-2">
          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter prompt with @Agent.field tokens..."
            className="text-xs h-24"
          />
          <div className="text-xs text-gray-600">
            Use @AgentName.field to reference upstream outputs
          </div>
        </div>
      ) : (
        <div className="text-xs text-gray-700">
          <div className="mb-1"><strong>Template:</strong></div>
          <div className="bg-white p-2 rounded border">
            {data.prompt_template || 'Double-click to edit prompt...'}
          </div>
        </div>
      )}
      
      {showTokenGuide && (
        <div className="mt-2 p-2 bg-white rounded text-xs">
          <div className="font-semibold mb-1">Token Reference:</div>
          <div className="space-y-1 text-gray-600">
            <div>@Agent.field → specific field</div>
            <div>@Agent.nested.field → nested</div>
            <div>@Agent.array[0] → array item</div>
          </div>
        </div>
      )}
      
      <div className="mt-2 flex items-center justify-between text-xs">
        <Badge variant="secondary" className="text-xs">
          Synthesizer
        </Badge>
        <div className="flex items-center space-x-1">
          <Activity className="h-3 w-3" />
          <span>Smart</span>
        </div>
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-500"
        isConnectable={isConnectable}
      />
    </div>
  )
}

const nodeTypes = {
  agentNode: AgentNode,
  moderatorNode: ModeratorNode
}

// ============= CUSTOM EDGE =============

const CustomEdge = ({ id, sourceX, sourceY, targetX, targetY, data }) => {
  const edgePath = `M ${sourceX},${sourceY} L ${targetX},${targetY}`
  
  return (
    <>
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={2}
        stroke={
          data?.compatibility_score >= 0.85 ? '#10b981' :
          data?.compatibility_score >= 0.7 ? '#f59e0b' :
          '#ef4444'
        }
        markerEnd="url(#arrowhead)"
      />
      {data?.compatibility_score !== undefined && (
        <text
          x={(sourceX + targetX) / 2}
          y={(sourceY + targetY) / 2 - 10}
          className="text-xs fill-gray-700 font-semibold"
          textAnchor="middle"
        >
          {Math.round(data.compatibility_score * 100)}%
        </text>
      )}
    </>
  )
}

// ============= MAIN COMPONENT =============

function EnhancedChainBuilderContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [agents, setAgents] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [executionResult, setExecutionResult] = useState(null)
  const [walletBalance, setWalletBalance] = useState(0)
  const [isExecuting, setIsExecuting] = useState(false)
  const { project } = useReactFlow()
  const wsRef = useRef(null)

  useEffect(() => {
    loadAgents()
    loadWalletBalance()
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = () => {
    const clientId = `client_${Date.now()}`
    wsRef.current = new WebSocket(`ws://localhost:8000/api/moderator/ws/${clientId}`)
    
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === 'node_updated') {
        setNodes((nds) => 
          nds.map((node) => 
            node.id === data.node_id ? { ...node, data: data.data } : node
          )
        )
      }
    }
    
    // Keep connection alive
    setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000)
  }

  const loadAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/agents')
      setAgents(response.data)
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const loadWalletBalance = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/wallet/balance')
      setWalletBalance(response.data.balance)
    } catch (error) {
      console.error('Failed to load wallet:', error)
    }
  }

  const loadRecommendations = async (nodeId) => {
    try {
      const response = await axios.get('http://localhost:8000/api/chain/recommend-agents')
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    }
  }

  const onConnect = useCallback(async (params) => {
    // Get source and target nodes
    const sourceNode = nodes.find(n => n.id === params.source)
    const targetNode = nodes.find(n => n.id === params.target)
    
    if (sourceNode && targetNode && targetNode.type !== 'moderatorNode') {
      // Check compatibility
      try {
        const response = await axios.post('http://localhost:8000/api/moderator/check-compatibility', {
          source_output: sourceNode.data.output_schema?.properties || {},
          target_input_schema: targetNode.data.input_schema || {}
        })
        
        const compatibility = response.data.compatibility
        
        if (compatibility.needs_moderator) {
          // Insert moderator node
          insertModeratorBetween(params.source, params.target, compatibility)
        } else {
          // Direct connection
          setEdges((eds) => addEdge({
            ...params,
            type: 'custom',
            data: { compatibility_score: compatibility.compatibility_score }
          }, eds))
        }
      } catch (error) {
        // Direct connection on error
        setEdges((eds) => addEdge(params, eds))
      }
    } else {
      // Direct connection for moderator nodes
      setEdges((eds) => addEdge(params, eds))
    }
  }, [nodes, setEdges])

  const insertModeratorBetween = (sourceId, targetId, compatibility) => {
    const sourceNode = nodes.find(n => n.id === sourceId)
    const targetNode = nodes.find(n => n.id === targetId)
    
    if (!sourceNode || !targetNode) return
    
    const moderatorId = `moderator_${Date.now()}`
    const moderatorNode = {
      id: moderatorId,
      type: 'moderatorNode',
      position: {
        x: (sourceNode.position.x + targetNode.position.x) / 2,
        y: (sourceNode.position.y + targetNode.position.y) / 2 + 50
      },
      data: {
        prompt_template: `Align @${sourceNode.data.name || sourceId} output to match ${targetNode.data.name || targetId} input requirements`,
        input_schema: sourceNode.data.output_schema || {},
        output_schema: targetNode.data.input_schema || {}
      }
    }
    
    // Add moderator node
    setNodes((nds) => [...nds, moderatorNode])
    
    // Add edges
    setEdges((eds) => [
      ...eds,
      {
        id: `${sourceId}-${moderatorId}`,
        source: sourceId,
        target: moderatorId,
        type: 'custom',
        data: { compatibility_score: 1.0 }
      },
      {
        id: `${moderatorId}-${targetId}`,
        source: moderatorId,
        target: targetId,
        type: 'custom',
        data: { compatibility_score: compatibility.synthesis_preview ? 0.95 : 0.85 }
      }
    ])
    
    // Create moderator in backend
    axios.post('http://localhost:8000/api/moderator/create', {
      node_id: moderatorId,
      name: 'Moderator',
      position: moderatorNode.position,
      prompt_template: moderatorNode.data.prompt_template,
      input_schema: moderatorNode.data.input_schema,
      output_schema: moderatorNode.data.output_schema,
      upstream_agents: [sourceId]
    })
  }

  const addAgentToChain = (agent) => {
    const newNode = {
      id: `agent_${agent.agent_id}_${Date.now()}`,
      type: 'agentNode',
      position: { 
        x: Math.random() * 400 + 100, 
        y: Math.random() * 300 + 100 
      },
      data: {
        ...agent,
        name: agent.name,
        description: agent.description,
        verification_level: agent.verification_level || 'L1',
        price_cents: agent.price_cents || 0
      }
    }
    
    setNodes((nds) => [...nds, newNode])
  }

  const duplicateModeratorNode = async (nodeId) => {
    const node = nodes.find(n => n.id === nodeId)
    if (!node || node.type !== 'moderatorNode') return
    
    try {
      const response = await axios.post(`http://localhost:8000/api/moderator/duplicate/${nodeId}`, {
        x: node.position.x + 100,
        y: node.position.y + 100
      })
      
      const newNode = {
        id: response.data.new_id,
        type: 'moderatorNode',
        position: response.data.node.position,
        data: response.data.node
      }
      
      setNodes((nds) => [...nds, newNode])
    } catch (error) {
      console.error('Failed to duplicate moderator:', error)
    }
  }

  const executeChain = async () => {
    setIsExecuting(true)
    
    try {
      // Build execution order using topological sort
      const executionOrder = topologicalSort(nodes, edges)
      
      // Execute nodes in order
      const outputs = {}
      let totalCost = 0
      
      for (const nodeId of executionOrder) {
        const node = nodes.find(n => n.id === nodeId)
        
        if (node.type === 'moderatorNode') {
          // Execute moderator
          const upstreamOutputs = {}
          edges.forEach(edge => {
            if (edge.target === nodeId && outputs[edge.source]) {
              upstreamOutputs[edge.source] = outputs[edge.source]
            }
          })
          
          const response = await axios.post('http://localhost:8000/api/moderator/execute', {
            node_id: nodeId,
            upstream_outputs: upstreamOutputs
          })
          
          outputs[nodeId] = response.data.output_generated
          totalCost += response.data.cost_cents || 0
        } else {
          // Execute regular agent
          // Mock execution for now
          outputs[nodeId] = {
            result: `Output from ${node.data.name}`,
            timestamp: new Date().toISOString()
          }
          totalCost += node.data.price_cents || 0
        }
      }
      
      setExecutionResult({
        success: true,
        outputs,
        totalCost,
        executionOrder
      })
      
      // Update wallet
      setWalletBalance(prev => prev - totalCost)
      
    } catch (error) {
      setExecutionResult({
        success: false,
        error: error.message
      })
    } finally {
      setIsExecuting(false)
    }
  }

  const topologicalSort = (nodes, edges) => {
    const sorted = []
    const visited = new Set()
    const visiting = new Set()
    
    const visit = (nodeId) => {
      if (visited.has(nodeId)) return
      if (visiting.has(nodeId)) throw new Error('Cyclic dependency detected')
      
      visiting.add(nodeId)
      
      // Visit dependencies first
      edges.forEach(edge => {
        if (edge.target === nodeId) {
          visit(edge.source)
        }
      })
      
      visiting.delete(nodeId)
      visited.add(nodeId)
      sorted.push(nodeId)
    }
    
    nodes.forEach(node => visit(node.id))
    
    return sorted
  }

  const saveChain = async () => {
    try {
      await axios.post('http://localhost:8000/api/chain/save', {
        chain_id: `chain_${Date.now()}`,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          data: e.data
        })),
        idempotency_key: `save_${Date.now()}`
      })
      
      alert('Chain saved successfully!')
    } catch (error) {
      alert('Failed to save chain: ' + error.message)
    }
  }

  const onNodeClick = (event, node) => {
    setSelectedNode(node)
    if (node.type === 'agentNode') {
      loadRecommendations(node.id)
    }
  }

  const onNodeDoubleClick = (event, node) => {
    if (node.type === 'moderatorNode') {
      // Double-click handled by ModeratorNode component
    }
  }

  const onNodeContextMenu = (event, node) => {
    event.preventDefault()
    
    if (node.type === 'moderatorNode') {
      if (confirm('Duplicate this moderator?')) {
        duplicateModeratorNode(node.id)
      }
    }
  }

  const filteredAgents = agents.filter(agent =>
    agent.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    agent.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="flex h-screen">
      {/* Left Panel - Agent Library */}
      <div className="w-80 bg-white border-r p-4 overflow-y-auto">
        <div className="mb-4">
          <h2 className="text-xl font-bold mb-3">Agent Library</h2>
          
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
            />
          </div>
          
          <Button 
            className="w-full mb-4"
            variant="outline"
            onClick={() => {
              const moderatorNode = {
                id: `moderator_${Date.now()}`,
                type: 'moderatorNode',
                position: { x: 250, y: 250 },
                data: {
                  prompt_template: '',
                  input_schema: {},
                  output_schema: {}
                }
              }
              setNodes((nds) => [...nds, moderatorNode])
            }}
          >
            <Zap className="h-4 w-4 mr-2" />
            Add Moderator Agent
          </Button>
        </div>
        
        <div className="space-y-2">
          {filteredAgents.map((agent) => (
            <Card 
              key={agent.agent_id}
              className="cursor-pointer hover:shadow-md transition-all"
              onClick={() => addAgentToChain(agent)}
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-semibold text-sm">{agent.name}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      {agent.description}
                    </div>
                  </div>
                  <Badge variant={agent.verification_level === 'L3' ? 'default' : 'secondary'} className="text-xs ml-2">
                    {agent.verification_level}
                  </Badge>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs">
                  <Badge variant="outline" className="text-xs">
                    {agent.type}
                  </Badge>
                  <div className="flex items-center space-x-1">
                    <DollarSign className="h-3 w-3" />
                    <span>{agent.price_cents}¢</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
        
        {recommendations.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold mb-2">Recommended Next</h3>
            <div className="space-y-2">
              {recommendations.map((rec) => (
                <Card 
                  key={rec.agent_id}
                  className="cursor-pointer hover:shadow-md transition-all bg-blue-50"
                  onClick={() => {
                    const agent = agents.find(a => a.agent_id === rec.agent_id)
                    if (agent) addAgentToChain(agent)
                  }}
                >
                  <CardContent className="p-2">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium">{rec.name}</div>
                      <Badge variant="secondary" className="text-xs">
                        {Math.round(rec.compatibility_score * 100)}%
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Main Canvas */}
      <div className="flex-1">
        {/* Top Bar */}
        <div className="bg-white border-b p-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold">Chain Builder</h1>
            <Badge variant="outline">
              Wallet: ${(walletBalance / 100).toFixed(2)}
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={saveChain}>
              <Save className="h-4 w-4 mr-2" />
              Save Chain
            </Button>
            <Button 
              onClick={executeChain}
              disabled={isExecuting || nodes.length === 0}
            >
              <Play className="h-4 w-4 mr-2" />
              {isExecuting ? 'Executing...' : 'Run Chain'}
            </Button>
          </div>
        </div>
        
        {/* React Flow Canvas */}
        <div className="h-full">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodeContextMenu={onNodeContextMenu}
            nodeTypes={nodeTypes}
            edgeTypes={{ custom: CustomEdge }}
            fitView
          >
            <Background />
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
                  <polygon
                    points="0 0, 10 5, 0 10"
                    fill="#666"
                  />
                </marker>
              </defs>
            </svg>
          </ReactFlow>
        </div>
        
        {/* Execution Result */}
        {executionResult && (
          <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-md">
            <h3 className="font-semibold mb-2">
              Execution {executionResult.success ? 'Complete' : 'Failed'}
            </h3>
            {executionResult.success ? (
              <div className="text-sm">
                <div>Cost: ${(executionResult.totalCost / 100).toFixed(2)}</div>
                <div>Nodes executed: {executionResult.executionOrder?.length || 0}</div>
              </div>
            ) : (
              <div className="text-sm text-red-600">
                Error: {executionResult.error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function EnhancedChainBuilder() {
  return (
    <ReactFlowProvider>
      <EnhancedChainBuilderContent />
    </ReactFlowProvider>
  )
}
