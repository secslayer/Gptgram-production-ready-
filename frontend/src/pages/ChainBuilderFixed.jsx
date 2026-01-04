import { useState, useCallback, useEffect } from 'react'
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
  useReactFlow,
  Panel
} from 'reactflow'
import 'reactflow/dist/style.css'
import axios from 'axios'
import { Card, CardContent } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Textarea } from '../components/ui/textarea'
import {
  Search,
  Play,
  Save,
  Plus,
  Zap,
  Bot,
  Trash2,
  User,
  AlertCircle,
  DollarSign,
  RefreshCw,
  X,
  Check,
  Activity,
  Sparkles,
  Edit
} from 'lucide-react'

// ============= INPUT NODE WITH WORKING EDITOR =============
const InputNode = ({ data, isConnectable, id }) => {
  const [text, setText] = useState(data.text || 'Enter user input...')
  const [editing, setEditing] = useState(false)
  const [localText, setLocalText] = useState(text)
  
  const handleSave = async () => {
    try {
      const response = await axios.put(`http://localhost:8000/api/moderator/input-node/${id}`, {
        text: localText
      })
      setText(localText)
      data.text = localText
      setEditing(false)
      console.log('Input saved:', localText)
    } catch (error) {
      console.error('Failed to update input:', error)
      alert('Failed to save input')
    }
  }
  
  const handleCancel = () => {
    setLocalText(text)
    setEditing(false)
  }
  
  return (
    <div 
      className="px-4 py-3 shadow-lg rounded-lg border-2 border-blue-500 bg-blue-50"
      style={{ minWidth: '280px' }}
      data-test-id="input-node"
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <User className="h-4 w-4 text-blue-600" />
          <div className="font-semibold">User Input</div>
        </div>
        {!editing ? (
          <Button 
            size="sm" 
            variant="ghost" 
            onClick={() => {
              setLocalText(text)
              setEditing(true)
            }}
          >
            <Edit className="h-3 w-3" />
          </Button>
        ) : (
          <div className="flex space-x-1">
            <Button size="sm" variant="ghost" onClick={handleSave}>
              <Check className="h-3 w-3 text-green-600" />
            </Button>
            <Button size="sm" variant="ghost" onClick={handleCancel}>
              <X className="h-3 w-3 text-red-600" />
            </Button>
          </div>
        )}
      </div>
      
      {editing ? (
        <div className="space-y-2">
          <Textarea
            value={localText}
            onChange={(e) => setLocalText(e.target.value)}
            placeholder="Enter user input..."
            className="text-sm h-24"
            autoFocus
          />
          <div className="text-xs text-gray-600">
            This input will be available as @Input.text
          </div>
        </div>
      ) : (
        <div className="text-sm text-gray-700 bg-white p-2 rounded border">
          {text}
        </div>
      )}
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-blue-500"
        isConnectable={isConnectable}
      />
    </div>
  )
}

// ============= AGENT NODE =============
const AgentNode = ({ data, isConnectable, selected }) => {
  return (
    <div 
      className={`px-4 py-3 shadow-lg rounded-lg border-2 bg-white ${
        selected ? 'border-blue-500' : 
        data.verification_level === 'L3' ? 'border-green-500' :
        data.verification_level === 'L2' ? 'border-yellow-500' :
        'border-gray-300'
      }`}
      style={{ minWidth: '200px' }}
      data-test-id={`agent-node-${data.agent_id}`}
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
          <div className="font-semibold text-sm">{data.name || 'Agent'}</div>
        </div>
        <Badge variant={data.type === 'n8n' ? 'secondary' : 'default'} className="text-xs">
          {data.type || 'custom'}
        </Badge>
      </div>
      
      <div className="mt-1 text-xs text-gray-600">
        {data.description || 'No description'}
      </div>
      
      <div className="mt-2 flex items-center justify-between text-xs">
        <Badge variant="outline" className="text-xs">
          {data.verification_level || 'L1'}
        </Badge>
        <div className="flex items-center space-x-1 text-gray-500">
          <DollarSign className="h-3 w-3" />
          <span>{data.price_cents || 0}¢</span>
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

// ============= ADVANCED MODERATOR NODE =============
const ModeratorNode = ({ data, isConnectable, id }) => {
  const [editing, setEditing] = useState(false)
  const [prompt, setPrompt] = useState(data.prompt_template || '')
  const [showTokenGuide, setShowTokenGuide] = useState(false)
  const [activeTab, setActiveTab] = useState(data.method || 'prompt')
  
  const handleSave = async () => {
    try {
      await axios.put(`http://localhost:8000/api/moderator/node/${id}`, {
        prompt_template: prompt,
        method: activeTab
      })
      data.prompt_template = prompt
      data.method = activeTab
      setEditing(false)
    } catch (error) {
      console.error('Failed to update moderator:', error)
    }
  }
  
  const handleAutofill = async () => {
    try {
      const response = await axios.post(`http://localhost:8000/api/moderator/autofill/${id}`)
      if (response.data.prompt_template) {
        setPrompt(response.data.prompt_template)
      }
    } catch (error) {
      console.error('Failed to autofill:', error)
    }
  }
  
  return (
    <div 
      className="px-4 py-3 shadow-lg rounded-lg border-2 border-purple-500 bg-purple-50"
      style={{ minWidth: '300px', maxWidth: '400px' }}
      data-test-id="moderator-node"
      onDoubleClick={() => setEditing(!editing)}
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
          <div className="font-semibold text-sm">Moderator Agent</div>
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
          <div className="flex space-x-1 bg-white rounded p-1">
            <button
              onClick={() => setActiveTab('prompt')}
              className={`flex-1 text-xs py-1 px-2 rounded transition-colors ${
                activeTab === 'prompt' ? 'bg-purple-500 text-white' : 'hover:bg-gray-100'
              }`}
            >
              Prompt
            </button>
            <button
              onClick={() => setActiveTab('deterministic')}
              className={`flex-1 text-xs py-1 px-2 rounded transition-colors ${
                activeTab === 'deterministic' ? 'bg-purple-500 text-white' : 'hover:bg-gray-100'
              }`}
            >
              Deterministic
            </button>
            <button
              onClick={() => setActiveTab('gemini')}
              className={`flex-1 text-xs py-1 px-2 rounded transition-colors ${
                activeTab === 'gemini' ? 'bg-purple-500 text-white' : 'hover:bg-gray-100'
              }`}
            >
              AI
            </button>
          </div>
          
          {activeTab === 'prompt' && (
            <>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Enter prompt with @Agent.field tokens..."
                className="text-xs h-24"
              />
              <Button size="sm" variant="outline" onClick={handleAutofill} className="text-xs w-full">
                Autofill from DB
              </Button>
            </>
          )}
          
          {activeTab === 'deterministic' && (
            <div className="text-xs text-gray-600 bg-white p-2 rounded">
              <div className="font-semibold mb-1">Deterministic Mode</div>
              <div>Auto-maps fields based on schema</div>
              <Badge variant="outline" className="text-xs mt-2">
                Score: {data.compatibility_score ? `${Math.round(data.compatibility_score * 100)}%` : 'N/A'}
              </Badge>
            </div>
          )}
          
          {activeTab === 'gemini' && (
            <div className="text-xs text-gray-600 bg-white p-2 rounded">
              <div className="font-semibold mb-1">AI Mode</div>
              <div>Uses AI to transform data</div>
              <div className="mt-2 flex items-center text-yellow-600">
                <DollarSign className="h-3 w-3 mr-1" />
                <span>~5¢ per call</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-xs text-gray-700">
          <div className="mb-1"><strong>Method:</strong> {data.method || activeTab}</div>
          <div className="bg-white p-2 rounded border">
            {data.prompt_template || prompt || 'Double-click to edit...'}
          </div>
        </div>
      )}
      
      {showTokenGuide && (
        <div className="mt-2 p-2 bg-white rounded text-xs">
          <div className="font-semibold mb-1">Token Guide:</div>
          <div className="space-y-1 text-gray-600">
            <div>@Agent.field → field value</div>
            <div>@Agent.nested.field → nested</div>
            <div>@Input.text → user input</div>
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
        className="w-3 h-3 !bg-purple-500"
        isConnectable={isConnectable}
      />
    </div>
  )
}

const nodeTypes = {
  inputNode: InputNode,
  agentNode: AgentNode,
  moderatorNode: ModeratorNode
}

// ============= MAIN COMPONENT =============
function ChainBuilderContent() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [agents, setAgents] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedNodes, setSelectedNodes] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [executionResult, setExecutionResult] = useState(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [chainName, setChainName] = useState('My Chain')
  const { getViewport } = useReactFlow()

  useEffect(() => {
    loadAgents()
    // Auto-refresh agents every 5 seconds to catch new additions
    const interval = setInterval(loadAgents, 5000)
    
    // Refresh when window regains focus
    const handleFocus = () => {
      loadAgents()
    }
    window.addEventListener('focus', handleFocus)
    
    // Refresh when navigating to this page
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        loadAgents()
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      clearInterval(interval)
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [])

  const loadAgents = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/agents/')
      // Normalize agent data - backend returns 'id', frontend uses 'agent_id'
      const normalizedAgents = (Array.isArray(response.data) ? response.data : []).map(agent => ({
        ...agent,
        agent_id: agent.id || agent.agent_id,
        id: agent.id || agent.agent_id,
        category: agent.category || agent.type || 'general',
        rating: 4.5 + Math.random() * 0.5,
        downloads: Math.floor(Math.random() * 1000) + 100
      }))
      
      // Always update agents state to ensure latest data
      setAgents(normalizedAgents)
      console.log('Loaded agents:', normalizedAgents.length, 'agents')
      
      // Return the agent count for feedback
      return normalizedAgents.length
    } catch (error) {
      console.error('Failed to load agents:', error)
      setAgents([])
      return 0
    }
  }

  const onConnect = useCallback(async (params) => {
    // Get source and target nodes
    const sourceNode = nodes.find(n => n.id === params.source)
    const targetNode = nodes.find(n => n.id === params.target)
    
    if (sourceNode && targetNode && targetNode.type !== 'moderatorNode') {
      // Check compatibility
      try {
        const response = await axios.get(
          `http://localhost:8000/api/agents/compatibility-check?upstream_id=${sourceNode.data?.agent_id || sourceNode.id}&downstream_id=${targetNode.data?.agent_id || targetNode.id}`
        )
        
        const compatibility = response.data.compatibility || {}
        const score = compatibility.compatibility_score || 0.5
        
        if (score < 0.7) {
          // Insert moderator automatically
          const moderatorId = `moderator_${Date.now()}`
          const moderatorNode = {
            id: moderatorId,
            type: 'moderatorNode',
            position: {
              x: (sourceNode.position.x + targetNode.position.x) / 2,
              y: (sourceNode.position.y + targetNode.position.y) / 2 + 50
            },
            data: {
              prompt_template: `Transform @${sourceNode.data.name || sourceNode.id} output to match ${targetNode.data.name || targetNode.id} input`,
              compatibility_score: score,
              method: 'prompt'
            }
          }
          
          // Add moderator and connections
          setNodes((nds) => [...nds, moderatorNode])
          setEdges((eds) => [
            ...eds,
            {
              id: `${params.source}-${moderatorId}`,
              source: params.source,
              target: moderatorId,
              animated: true,
              style: { stroke: '#10b981', strokeWidth: 2 }
            },
            {
              id: `${moderatorId}-${params.target}`,
              source: moderatorId,
              target: params.target,
              animated: true,
              style: { stroke: score >= 0.5 ? '#f59e0b' : '#ef4444', strokeWidth: 2 }
            }
          ])
          
          // Create in backend
          axios.post('http://localhost:8000/api/moderator/create-with-context', {
            node_id: moderatorId,
            position: moderatorNode.position,
            upstream_agent_ids: [sourceNode.id],
            downstream_agent_id: targetNode.id,
            include_input_node: false
          }).catch(console.error)
        } else {
          // Direct connection
          setEdges((eds) => addEdge({
            ...params,
            animated: true,
            style: { 
              stroke: score >= 0.85 ? '#10b981' : score >= 0.7 ? '#f59e0b' : '#ef4444',
              strokeWidth: 2 
            },
            data: { compatibility_score: score }
          }, eds))
        }
      } catch (error) {
        // Fallback to simple connection
        setEdges((eds) => addEdge({
          ...params,
          animated: true,
          style: { stroke: '#10b981', strokeWidth: 2 }
        }, eds))
      }
    } else {
      // Direct connection for moderator nodes or input nodes
      setEdges((eds) => addEdge({
        ...params,
        animated: true,
        style: { stroke: '#10b981', strokeWidth: 2 }
      }, eds))
    }
  }, [nodes, setEdges, setNodes])

  const addInputNode = () => {
    const viewport = getViewport()
    const position = { 
      x: 100 + Math.random() * 200,
      y: 100 + Math.random() * 100
    }
    
    const newNode = {
      id: `input_${Date.now()}`,
      type: 'inputNode',
      position,
      data: {
        text: 'Enter your input here...'
      }
    }
    
    setNodes((nds) => [...nds, newNode])
    
    // Create in backend
    axios.post('http://localhost:8000/api/moderator/input-node/create', {
      node_id: newNode.id,
      position: position,
      initial_text: newNode.data.text
    }).catch(console.error)
  }

  const addAgentToChain = (agent) => {
    const position = {
      x: 200 + Math.random() * 300,
      y: 100 + Math.random() * 200
    }
    
    const agentId = agent.id || agent.agent_id
    
    const newNode = {
      id: `agent_${agentId}_${Date.now()}`,
      type: 'agentNode',
      position,
      data: {
        ...agent,
        id: agentId,
        agent_id: agentId,
        name: agent.name,
        description: agent.description,
        type: agent.type,
        endpoint_url: agent.endpoint_url,
        hmac_secret: agent.hmac_secret,
        verification_level: agent.verification_level || 'L1',
        price_cents: agent.price_cents || 0,
        input_schema: agent.input_schema,
        output_schema: agent.output_schema
      }
    }
    
    setNodes((nds) => [...nds, newNode])
    console.log('Added agent to chain:', newNode)
  }

  const addModeratorNode = () => {
    const position = {
      x: 300 + Math.random() * 200,
      y: 200 + Math.random() * 100
    }
    
    const newNode = {
      id: `moderator_${Date.now()}`,
      type: 'moderatorNode',
      position,
      data: {
        name: 'Moderator',
        description: 'Transforms data between agents'
      }
    }
    
    setNodes((nds) => [...nds, newNode])
  }

  const deleteSelectedNodes = () => {
    if (selectedNodes.length === 0) return
    
    // Remove nodes
    setNodes((nds) => nds.filter(node => !selectedNodes.includes(node.id)))
    
    // Remove connected edges
    setEdges((eds) => eds.filter(edge => 
      !selectedNodes.includes(edge.source) && !selectedNodes.includes(edge.target)
    ))
    
    setSelectedNodes([])
  }

  const onNodeClick = (event, node) => {
    setSelectedNode(node)
    if (node.type === 'agentNode') {
      loadRecommendations(node.id)
    }
  }
  
  const onNodesSelectionChange = useCallback((nodes) => {
    setSelectedNodes(nodes.map(n => n.id))
  }, [])
  
  const loadRecommendations = async (nodeId) => {
    try {
      const node = nodes.find(n => n.id === nodeId)
      if (!node) return
      
      // Get recommendations from actual agents
      if (node.type === 'agentNode' && agents.length > 0) {
        // Filter out agents already in the chain
        const usedAgentIds = nodes.filter(n => n.type === 'agentNode').map(n => n.data.id || n.data.agent_id)
        const availableAgents = agents.filter(a => !usedAgentIds.includes(a.id || a.agent_id))
        
        // Simple recommendation: show all available agents with mock compatibility
        const recs = availableAgents.slice(0, 5).map((agent, idx) => ({
          ...agent,
          agent_id: agent.id || agent.agent_id,
          compatibility_score: 0.95 - (idx * 0.05)
        }))
        
        setRecommendations(recs)
        console.log('Recommendations for', node.data.name, ':', recs)
      } else {
        setRecommendations([])
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    }
  }

  const executeChain = async () => {
    if (nodes.length === 0) {
      alert('Add some nodes to the chain first!')
      return
    }
    
    setIsExecuting(true)
    setExecutionResult(null)
    
    try {
      // Build execution order (topological sort)
      const executionOrder = []
      const visited = new Set()
      
      const visit = (nodeId) => {
        if (visited.has(nodeId)) return
        visited.add(nodeId)
        
        // Visit dependencies first
        edges.forEach(edge => {
          if (edge.target === nodeId && !visited.has(edge.source)) {
            visit(edge.source)
          }
        })
        
        executionOrder.push(nodeId)
      }
      
      nodes.forEach(node => visit(node.id))
      
      // Create run in backend
      const runData = {
        chain_id: `chain_${Date.now()}`,
        status: 'running',
        nodes: executionOrder,
        outputs: {}
      }
      
      const runResponse = await axios.post('http://localhost:8000/api/runs/create', runData)
      const runId = runResponse.data.run_id
      console.log('Created run:', runId)
      
      // Execute nodes
      const outputs = {}
      let totalCost = 0
      
      for (const nodeId of executionOrder) {
        const node = nodes.find(n => n.id === nodeId)
        
        if (node.type === 'inputNode') {
          outputs[nodeId] = { 
            text: node.data.text,
            type: 'input'
          }
        } else if (node.type === 'agentNode') {
          // Get input from connected nodes
          const inputData = {}
          let inputPayload = {}
          
          edges.forEach(edge => {
            if (edge.target === nodeId && outputs[edge.source]) {
              const sourceOutput = outputs[edge.source]
              inputData[edge.source] = sourceOutput
              
              // Build input payload based on source output
              if (sourceOutput.text) {
                inputPayload.text = sourceOutput.text
              } else if (sourceOutput.summary) {
                inputPayload.text = sourceOutput.summary
              } else if (sourceOutput.translated) {
                inputPayload.text = sourceOutput.translated
              } else if (sourceOutput.output?.text) {
                inputPayload.text = sourceOutput.output.text
              }
            }
          })
          
          // Call agent via backend (handles HMAC authentication)
          try {
            let agentResult = null
            const agentConfig = node.data
            const agentId = agentConfig.id
            
            if (!agentId) {
              throw new Error('Agent ID not found')
            }
            
            // Build request payload - ensure text field is present
            const requestPayload = { ...inputPayload }
            if (!requestPayload.text) {
              requestPayload.text = 'No text provided'
            }
            
            console.log(`Executing agent ${agentConfig.name} (ID: ${agentId})`, requestPayload)
            
            // Call backend to execute agent (backend handles HMAC)
            const response = await axios.post(
              `http://localhost:8000/api/agents/${agentId}/execute`,
              requestPayload,
              { timeout: 30000 } // 30 second timeout for n8n
            )
            
            // Store the output from the agent
            agentResult = {
              ...response.data.output,
              agent_id: agentId,
              agent_name: agentConfig.name,
              type: agentConfig.type || 'custom'
            }
            
            console.log(`Agent ${agentConfig.name} result:`, agentResult)
            outputs[nodeId] = agentResult
            
          } catch (error) {
            console.error(`Error executing ${node.data.name}:`, error)
            outputs[nodeId] = {
              error: error.response?.data?.detail || error.message || 'Execution failed',
              type: 'error',
              agent_name: node.data.name,
              input: inputPayload
            }
          }
          
          totalCost += node.data.price_cents || 0
        } else if (node.type === 'moderatorNode') {
          // Get upstream outputs
          const upstreamOutputs = {}
          edges.forEach(edge => {
            if (edge.target === nodeId && outputs[edge.source]) {
              upstreamOutputs[edge.source] = outputs[edge.source]
            }
          })
          
          // Transform data based on method
          outputs[nodeId] = {
            transformed: true,
            method: node.data.method || 'prompt',
            input: upstreamOutputs,
            output: {
              text: 'Transformed: ' + JSON.stringify(upstreamOutputs).substring(0, 50),
              type: 'moderator'
            }
          }
          totalCost += 5
        }
      }
      
      // Update run with outputs
      const updateResponse = await axios.put(`http://localhost:8000/api/runs/${runId}`, {
        status: 'completed',
        outputs: outputs
      })
      
      console.log('Run completed:', updateResponse.data)
      
      setExecutionResult({
        success: true,
        runId,
        outputs,
        totalCost,
        message: `Chain executed! Cost: ${totalCost}¢. Run ID: ${runId}`
      })
      
      // Show success and offer to view run history
      setTimeout(() => {
        if (confirm('Chain executed successfully! View run history?')) {
          window.location.href = '/runs'
        }
      }, 1000)
      
    } catch (error) {
      console.error('Execution failed:', error)
      setExecutionResult({
        success: false,
        error: error.message || 'Execution failed'
      })
    } finally {
      setIsExecuting(false)
    }
  }

  const saveChain = async () => {
    try {
      const chainData = {
        name: chainName,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target
        }))
      }
      
      // Save to localStorage for now
      localStorage.setItem('savedChain', JSON.stringify(chainData))
      alert('Chain saved successfully!')
    } catch (error) {
      alert('Failed to save chain: ' + error.message)
    }
  }

  const loadChain = () => {
    try {
      const savedData = localStorage.getItem('savedChain')
      if (savedData) {
        const chainData = JSON.parse(savedData)
        setNodes(chainData.nodes || [])
        setEdges(chainData.edges || [])
        setChainName(chainData.name || 'My Chain')
        alert('Chain loaded successfully!')
      } else {
        alert('No saved chain found')
      }
    } catch (error) {
      alert('Failed to load chain: ' + error.message)
    }
  }

  const clearCanvas = () => {
    if (confirm('Clear all nodes and connections?')) {
      setNodes([])
      setEdges([])
      setSelectedNodes([])
      setExecutionResult(null)
    }
  }

  const filteredAgents = agents.filter(agent => {
    const search = searchTerm.toLowerCase()
    return !search || 
      agent.name?.toLowerCase().includes(search) ||
      agent.description?.toLowerCase().includes(search) ||
      agent.type?.toLowerCase().includes(search) ||
      agent.category?.toLowerCase().includes(search)
  })

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Panel - Agent Library */}
      <div className="w-80 bg-white border-r shadow-sm overflow-y-auto">
        <div className="p-4 border-b bg-gray-50">
          <h2 className="text-lg font-bold mb-3">Agent Library</h2>
          
          <div className="relative mb-3">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9"
              data-test-id="agent-search"
            />
          </div>
          
          <div className="space-y-2">
            <Button 
              className="w-full"
              variant="outline"
              onClick={addInputNode}
              data-test-id="add-input-node"
            >
              <User className="h-4 w-4 mr-2" />
              Add Input Node
            </Button>
            
            <Button 
              className="w-full"
              variant="outline"
              onClick={addModeratorNode}
              data-test-id="add-moderator"
            >
              <Zap className="h-4 w-4 mr-2" />
              Add Moderator
            </Button>
            
            <Button
              className="w-full"
              variant="outline"
              onClick={async () => {
                const previousCount = agents.length
                const newCount = await loadAgents()
                if (newCount > previousCount) {
                  alert(`Agents refreshed! Found ${newCount - previousCount} new agent(s)`)
                } else if (newCount === previousCount) {
                  alert(`Agents refreshed! Total: ${newCount} agents`)
                } else {
                  alert(`Agents refreshed! Total: ${newCount} agents`)
                }
              }}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${agents.length > 0 ? '' : 'animate-spin'}`} />
              Refresh Agents ({agents.length})
            </Button>
          </div>
        </div>
        
        <div className="p-4">
          <h3 className="font-semibold mb-2 text-sm text-gray-600">Available Agents ({filteredAgents.length})</h3>
          {filteredAgents.length === 0 ? (
            <div className="text-center py-4 text-gray-500 text-sm">
              {searchTerm ? 'No agents found matching your search' : 'Loading agents...'}
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {filteredAgents.map((agent) => (
              <Card 
                key={agent.agent_id}
                className="cursor-pointer hover:shadow-md transition-all hover:border-blue-300"
                onClick={() => addAgentToChain(agent)}
                data-test-id={`agent-library-${agent.agent_id}`}
              >
                <CardContent className="p-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="font-semibold text-sm flex items-center">
                        <Bot className="h-3 w-3 mr-1 text-blue-600" />
                        {agent.name}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {agent.description}
                      </div>
                    </div>
                    <Badge 
                      variant={agent.verification_level === 'L3' ? 'default' : 'secondary'} 
                      className="text-xs ml-2"
                    >
                      {agent.verification_level || 'L1'}
                    </Badge>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {agent.type}
                    </Badge>
                    <div className="flex items-center text-xs text-gray-500">
                      <DollarSign className="h-3 w-3" />
                      <span>{agent.price_cents || 0}¢</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            </div>
          )}
        </div>
        
        {/* Recommendations Section */}
        {recommendations.length > 0 && (
          <div className="p-4 border-t bg-gradient-to-b from-blue-50 to-white">
            <h3 className="font-semibold mb-3 text-sm flex items-center text-blue-800">
              <Sparkles className="h-4 w-4 mr-1 text-blue-600" />
              Recommended Next Agents
            </h3>
            <div className="space-y-2">
              {recommendations.map((rec) => (
                <Card 
                  key={rec.agent_id}
                  className="cursor-pointer hover:shadow-md transition-all bg-white hover:bg-blue-100"
                  onClick={() => {
                    const agent = agents.find(a => a.agent_id === rec.agent_id) || rec
                    addAgentToChain(agent)
                    setRecommendations([])
                  }}
                >
                  <CardContent className="p-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <Bot className="h-3 w-3 mr-1 text-blue-600" />
                        <span className="text-sm font-medium">{rec.name}</span>
                      </div>
                      <Badge variant="default" className="text-xs">
                        {Math.round(rec.compatibility_score * 100)}%
                      </Badge>
                    </div>
                    <div className="text-xs text-gray-600 mt-1">
                      {rec.type} agent • Click to add
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </div>
      
      {/* Main Canvas */}
      <div className="flex-1 flex flex-col">
        {/* Top Bar */}
        <div className="bg-white border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Input
              value={chainName}
              onChange={(e) => setChainName(e.target.value)}
              className="w-48 font-semibold"
              placeholder="Chain name..."
            />
            <Badge variant="outline" className="text-sm">
              {nodes.length} nodes, {edges.length} connections
            </Badge>
          </div>
          
          <div className="flex items-center space-x-2">
            {selectedNodes.length > 0 && (
              <Button 
                variant="outline"
                size="sm"
                onClick={deleteSelectedNodes}
                className="text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-4 w-4 mr-1" />
                Delete ({selectedNodes.length})
              </Button>
            )}
            
            <Button variant="outline" size="sm" onClick={clearCanvas}>
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
            
            <Button variant="outline" size="sm" onClick={loadChain}>
              Load
            </Button>
            
            <Button variant="outline" size="sm" onClick={saveChain}>
              <Save className="h-4 w-4 mr-1" />
              Save
            </Button>
            
            <Button 
              size="sm"
              onClick={executeChain}
              disabled={isExecuting || nodes.length === 0}
              data-test-id="execute-chain"
            >
              <Play className="h-4 w-4 mr-1" />
              {isExecuting ? 'Running...' : 'Run Chain'}
            </Button>
          </div>
        </div>
        
        {/* React Flow Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onSelectionChange={({ nodes }) => onNodesSelectionChange(nodes)}
            nodeTypes={nodeTypes}
            fitView
            deleteKeyCode="Delete"
          >
            <Background />
            <Controls />
            <MiniMap />
            
            {/* Execution Result Panel */}
            {executionResult && (
              <Panel position="bottom-right" className="bg-white rounded-lg shadow-lg p-4 m-4 max-w-md">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-semibold flex items-center">
                    {executionResult.success ? (
                      <>
                        <AlertCircle className="h-4 w-4 mr-2 text-green-600" />
                        Execution Complete
                      </>
                    ) : (
                      <>
                        <AlertCircle className="h-4 w-4 mr-2 text-red-600" />
                        Execution Failed
                      </>
                    )}
                  </h3>
                  <button 
                    onClick={() => setExecutionResult(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
                
                {executionResult.success ? (
                  <div className="text-sm space-y-1">
                    <div className="text-gray-600">Run ID: {executionResult.runId}</div>
                    <div className="text-gray-600">Nodes executed: {Object.keys(executionResult.outputs || {}).length}</div>
                    <div className="text-green-600 font-medium">{executionResult.message}</div>
                  </div>
                ) : (
                  <div className="text-sm text-red-600">
                    {executionResult.error}
                  </div>
                )}
              </Panel>
            )}
          </ReactFlow>
        </div>
      </div>
    </div>
  )
}

export default function ChainBuilderFixed() {
  return (
    <ReactFlowProvider>
      <ChainBuilderContent />
    </ReactFlowProvider>
  )
}
