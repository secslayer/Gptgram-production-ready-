import { useState, useCallback, useEffect } from 'react'
import axios from 'axios'
import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  Position,
  Handle
} from 'react-flow-renderer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import TransformerModal from '../components/TransformerModal'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import {
  Bot,
  GitBranch,
  Play,
  Save,
  Plus,
  Settings,
  Zap,
  DollarSign,
  AlertCircle,
  CheckCircle,
  ChevronRight,
  Loader2,
  Search,
  Shield
} from 'lucide-react'

// Custom node component
const AgentNode = ({ data, isConnectable }) => {
  const getVerificationColor = (level) => {
    switch (level) {
      case 'L3': return 'border-green-500 bg-green-50'
      case 'L2': return 'border-blue-500 bg-blue-50'
      case 'L1': return 'border-gray-500 bg-gray-50'
      default: return 'border-yellow-500 bg-yellow-50'
    }
  }

  return (
    <div className={`px-4 py-3 shadow-lg rounded-lg border-2 ${getVerificationColor(data.verificationLevel)} min-w-[200px]`}>
      <Handle
        type="target"
        position={Position.Left}
        isConnectable={isConnectable}
        style={{ background: '#555', width: 12, height: 12 }}
      />
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <Bot className="h-5 w-5" />
          <span className="font-semibold text-sm">{data.label}</span>
        </div>
        <Badge variant="outline" className="text-xs">
          {data.verificationLevel}
        </Badge>
      </div>
      {data.description && (
        <p className="text-xs text-gray-600 mb-2">{data.description}</p>
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
        style={{ background: '#555', width: 12, height: 12 }}
      />
    </div>
  )
}

const nodeTypes = {
  agentNode: AgentNode
}

export default function CompleteChainBuilder() {
  const [showTransformerModal, setShowTransformerModal] = useState(false)
  const [transformerSource, setTransformerSource] = useState(null)
  const [transformerTarget, setTransformerTarget] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const [executionStep, setExecutionStep] = useState(0)
  const [searchQuery, setSearchQuery] = useState('')
  const [chainName, setChainName] = useState('My Chain')
  
  const loadRecommendations = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/chain/recommend-agents', {
        context_node_ids: [selectedNode?.id],
        top_k: 5
      })
      setRecommendations(response.data)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    }
  }
  
  // Load recommendations when a node is selected
  useEffect(() => {
    if (selectedNode && selectedNode.id !== '1') {
      loadRecommendations()
    }
  }, [selectedNode])
  
  const handleTransformerAccept = (transformData) => {
    // Insert transformer node between source and target
    const transformerNode = {
      id: `transformer-${Date.now()}`,
      type: 'agentNode',
      position: {
        x: (transformerSource.position.x + transformerTarget.position.x) / 2,
        y: (transformerSource.position.y + transformerTarget.position.y) / 2
      },
      data: {
        label: 'Transformer',
        description: `${transformData.method} transform`,
        verificationLevel: 'AUTO',
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
      id: `e-${transformerSource.id}-${transformerNode.id}`,
      source: transformerSource.id,
      target: transformerNode.id,
      type: 'default',
      animated: true,
      style: { stroke: '#22c55e', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#22c55e' },
      label: '100%',
      labelStyle: { fontSize: 12, fontWeight: 600 }
    }
    
    const edge2 = {
      id: `e-${transformerNode.id}-${transformerTarget.id}`,
      source: transformerNode.id,
      target: transformerTarget.id,
      type: 'default',
      animated: true,
      style: { stroke: '#22c55e', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#22c55e' },
      label: `${Math.round(transformData.score * 100)}%`,
      labelStyle: { fontSize: 12, fontWeight: 600 }
    }
    
    setEdges(eds => [...eds, edge1, edge2])
  }
  
  const [nodes, setNodes, onNodesChange] = useNodesState([
    {
      id: '1',
      type: 'agentNode',
      position: { x: 100, y: 100 },
      data: {
        label: 'Input',
        description: 'Chain input',
        verificationLevel: 'SYSTEM',
        price: 0,
        type: 'system'
      }
    }
  ])
  
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  
  const availableAgents = [
    {
      id: 'summarizer',
      name: 'n8n Text Summarizer',
      type: 'n8n',
      description: 'Summarizes text',
      verificationLevel: 'L2',
      price: 50,
      inputSchema: { text: 'string', maxSentences: 'number' },
      outputSchema: { summary: 'string' }
    },
    {
      id: 'sentiment',
      name: 'Sentiment Analyzer',
      type: 'custom',
      description: 'Analyzes sentiment',
      verificationLevel: 'L3',
      price: 30,
      inputSchema: { text: 'string' },
      outputSchema: { sentiment: 'string', score: 'number' }
    },
    {
      id: 'translator',
      name: 'n8n Translator',
      type: 'n8n',
      description: 'Translates text',
      verificationLevel: 'L2',
      price: 75,
      inputSchema: { text: 'string', target: 'string' },
      outputSchema: { translated: 'string', target: 'string' }
    }
  ]

  const onConnect = useCallback(async (params) => {
    const sourceNode = nodes.find(n => n.id === params.source)
    const targetNode = nodes.find(n => n.id === params.target)
    
    // Calculate compatibility via API
    try {
      const response = await axios.post('http://localhost:8000/api/chain/compatibility-score', {
        source_agent_id: sourceNode?.id,
        target_agent_id: targetNode?.id,
        source_sample_output: sourceNode?.data.outputSchema || {}
      })
      
      const compatibilityScore = response.data.score
      
      // If score is low, offer to insert transformer
      if (compatibilityScore < 0.7) {
        setTransformerSource(sourceNode)
        setTransformerTarget(targetNode)
        setShowTransformerModal(true)
        return
      }
      
      // Otherwise create direct connection
      let edgeColor = '#22c55e' // green
      if (compatibilityScore < 0.4) edgeColor = '#ef4444' // red
      else if (compatibilityScore < 0.7) edgeColor = '#eab308' // yellow
      
      const newEdge = {
        ...params,
        type: 'default',
        animated: true,
        style: { stroke: edgeColor, strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: edgeColor },
        label: `${Math.round(compatibilityScore * 100)}%`,
        labelStyle: { fontSize: 12, fontWeight: 600 },
        data: { score: compatibilityScore }
      }
      
      setEdges((eds) => addEdge(newEdge, eds))
    } catch (error) {
      console.error('Failed to check compatibility:', error)
    }
  }, [nodes, setEdges])

  const addAgentToCanvas = (agent) => {
    const newNode = {
      id: `node-${Date.now()}`,
      type: 'agentNode',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 100 },
      data: {
        label: agent.name,
        description: agent.description,
        verificationLevel: agent.verificationLevel,
        price: agent.price,
        type: agent.type,
        inputSchema: agent.inputSchema,
        outputSchema: agent.outputSchema
      }
    }
    setNodes((nds) => nds.concat(newNode))
  }

  const calculateTotalCost = () => {
    return nodes.reduce((sum, node) => sum + (node.data.price || 0), 0)
  }

  const runChain = async () => {
    setIsRunning(true)
    setExecutionStep(0)
    
    // Simulate chain execution
    for (let i = 0; i < nodes.length; i++) {
      setExecutionStep(i + 1)
      await new Promise(resolve => setTimeout(resolve, 1500))
    }
    
    setIsRunning(false)
    setExecutionStep(0)
  }

  const saveChain = () => {
    const chainDescriptor = {
      nodes: nodes.map(n => ({
        node_id: n.id,
        agent_name: n.data.label,
        verification_level: n.data.verificationLevel,
        price: n.data.price
      })),
      edges: edges.map(e => ({
        from_node: e.source,
        to_node: e.target,
        compatibility_score: parseFloat(e.label) / 100 || 0.85
      })),
      merge_strategy: 'authoritative'
    }
    
    console.log('Saving chain:', chainDescriptor)
    // TODO: Send to backend
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
                    <span className="text-xs">${(agent.price / 100).toFixed(2)}</span>
                    {agent.type === 'n8n' && (
                      <Badge variant="secondary" className="text-xs">n8n</Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
          
          <Card className="bg-muted">
            <CardContent className="p-3">
              <h3 className="font-medium text-sm mb-2">How to use</h3>
              <ol className="text-xs space-y-1 text-muted-foreground">
                <li>1. Click agents to add to canvas</li>
                <li>2. Drag to connect nodes</li>
                <li>3. Check compatibility scores</li>
                <li>4. Run or save your chain</li>
              </ol>
            </CardContent>
          </Card>
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
                {nodes.length - 1} agents
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
            nodes={nodes.map((node, index) => ({
              ...node,
              style: {
                ...(isRunning && executionStep === index + 1 ? {
                  boxShadow: '0 0 0 3px #10b981'
                } : {})
              }
            }))}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={(event, node) => setSelectedNode(node)}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background variant="dots" gap={12} size={1} />
            <Controls />
            <MiniMap />
          </ReactFlow>
          
          {/* Legend */}
          <Card className="absolute bottom-4 left-4 w-64">
            <CardContent className="p-3">
              <h4 className="font-medium text-sm mb-2">Compatibility Scores</h4>
              <div className="space-y-1 text-xs">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded" />
                  <span>High (&gt;70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded" />
                  <span>Medium (40-70%)</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded" />
                  <span>Low (&lt;40%)</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Execution Status */}
          {isRunning && (
            <Card className="absolute top-4 right-4 w-64">
              <CardContent className="p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="font-medium text-sm">Executing Chain</span>
                </div>
                <div className="space-y-1">
                  {nodes.map((node, index) => (
                    <div key={node.id} className="flex items-center space-x-2 text-xs">
                      {executionStep > index ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : executionStep === index + 1 ? (
                        <Loader2 className="h-3 w-3 animate-spin" />
                      ) : (
                        <div className="h-3 w-3 border rounded-full" />
                      )}
                      <span>{node.data.label}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Right Sidebar - Node Inspector */}
      {selectedNode && (
        <div className="w-80 border-l bg-background p-4">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold mb-2">Node Inspector</h2>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{selectedNode.data.label}</CardTitle>
                  <CardDescription>{selectedNode.data.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium mb-1">Verification Level</p>
                      <Badge>{selectedNode.data.verificationLevel}</Badge>
                    </div>
                    
                    <div>
                      <p className="text-sm font-medium mb-1">Price</p>
                      <p className="text-lg font-semibold">
                        ${(selectedNode.data.price / 100).toFixed(2)}
                      </p>
                    </div>
                    
                    {selectedNode.data.inputSchema && (
                      <div>
                        <p className="text-sm font-medium mb-1">Input Schema</p>
                        <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                          {JSON.stringify(selectedNode.data.inputSchema, null, 2)}
                        </pre>
                      </div>
                    )}
                    
                    {selectedNode.data.outputSchema && (
                      <div>
                        <p className="text-sm font-medium mb-1">Output Schema</p>
                        <pre className="text-xs bg-muted p-2 rounded overflow-auto">
                          {JSON.stringify(selectedNode.data.outputSchema, null, 2)}
                        </pre>
                      </div>
                    )}
                    
                    <Button
                      variant="destructive"
                      size="sm"
                      className="w-full"
                      onClick={() => {
                        setNodes(nds => nds.filter(n => n.id !== selectedNode.id))
                        setEdges(eds => eds.filter(e => e.source !== selectedNode.id && e.target !== selectedNode.id))
                        setSelectedNode(null)
                      }}
                    >
                      Remove Node
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      )}
      
      {/* Recommendations Panel */}
      {recommendations.length > 0 && selectedNode && (
        <div className="absolute bottom-20 right-4 w-80">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Recommended Next Agents</CardTitle>
              <CardDescription>Based on historical success patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {recommendations.map(rec => (
                  <div
                    key={rec.agent_id}
                    className="p-2 border rounded-lg hover:bg-muted cursor-pointer"
                    onClick={() => {
                      const newAgent = {
                        id: rec.agent_id,
                        name: rec.name,
                        description: rec.reasons.join(', '),
                        verificationLevel: 'L2',
                        price: 50,
                        type: 'recommended'
                      }
                      addAgentToCanvas(newAgent)
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
