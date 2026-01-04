import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import {
  PlayCircle,
  Clock,
  DollarSign,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  Activity,
  GitBranch,
  Eye,
  Download,
  RefreshCw,
  Zap,
  FileText,
  Hash,
  Calendar,
  TrendingUp
} from 'lucide-react'

export default function CompleteRuns() {
  const [expandedNodes, setExpandedNodes] = useState({})
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  
  // Load runs from backend
  useEffect(() => {
    loadRuns()
  }, [])
  
  const loadRuns = async () => {
    try {
      setLoading(true)
      const response = await axios.get('http://localhost:8000/api/runs/')
      
      // Transform backend data to match component format
      const transformedRuns = response.data.map(run => ({
        id: run.run_id,
        runId: run.run_id,
        chainName: run.chain_id || 'Unnamed Chain',
        status: run.status === 'completed' ? 'succeeded' : run.status === 'failed' ? 'failed' : 'running',
        startedAt: run.started_at || new Date().toISOString(),
        completedAt: run.completed_at || (run.status === 'completed' ? new Date().toISOString() : null),
        duration: run.completed_at && run.started_at ? 
          Math.abs(new Date(run.completed_at) - new Date(run.started_at)) : 0,
        totalCost: run.total_cost || 0,
        nodes: run.nodes || [],
        input: run.outputs?.[run.nodes?.[0]] || {},
        output: run.outputs || {},
        error: run.error
      }))
      
      setRuns(transformedRuns)
      console.log('Loaded runs:', transformedRuns)
    } catch (error) {
      console.error('Failed to load runs:', error)
      // Keep mock data as fallback
      setRuns([
    {
      id: 'run-001',
      chainName: 'Text Processing Pipeline',
      status: 'succeeded',
      startedAt: '2025-10-31T10:30:45Z',
      completedAt: '2025-10-31T10:30:48Z',
      duration: 3200,
      totalCost: 155,
      nodes: [
        {
          id: 'node-1',
          name: 'n8n Summarizer',
          status: 'completed',
          duration: 1200,
          cost: 50,
          method: 'direct',
          confidence: 0.95,
          input: { text: 'AI is revolutionizing industries...', maxSentences: 2 },
          output: { summary: 'AI is transforming various sectors. Companies are adopting it rapidly.' }
        },
        {
          id: 'node-2',
          name: 'Sentiment Analyzer',
          status: 'completed',
          duration: 800,
          cost: 30,
          method: 'deterministic',
          mappingUsed: 'summary_text -> text',
          confidence: 0.88,
          input: { text: 'AI is transforming various sectors. Companies are adopting it rapidly.' },
          output: { sentiment: 'positive', score: 0.88 }
        },
        {
          id: 'node-3',
          name: 'Translator',
          status: 'completed',
          duration: 1200,
          cost: 75,
          method: 'llm',
          confidence: 0.92,
          input: { text: 'AI is transforming various sectors. Companies are adopting it rapidly.', target: 'es' },
          output: { translated: 'La IA está transformando varios sectores. Las empresas la están adoptando rápidamente.' }
        }
      ],
      input: {
        text: "Artificial intelligence is transforming industries worldwide. Machine learning algorithms can now process vast amounts of data in seconds.",
        maxSentences: 2
      },
      output: {
        summary: "AI is transforming industries globally.",
        sentiment: "positive",
        translation: "La IA está transformando las industrias a nivel mundial.",
        _provenance: {
          summary: {
            origin: 'node-1',
            method: 'direct',
            confidence: 0.95,
            transformChain: ['node-1']
          },
          sentiment: {
            origin: 'node-2',
            method: 'deterministic',
            confidence: 0.88,
            transformChain: ['node-2', 'mapping_hint']
          },
          translation: {
            origin: 'node-3',
            method: 'direct',
            confidence: 0.92,
            transformChain: ['node-3']
          }
        }
      }
    },
    {
      id: 'run-002',
      chainName: 'Sentiment Analysis Chain',
      status: 'failed',
      startedAt: '2025-10-31T09:15:22Z',
      completedAt: '2025-10-31T09:15:25Z',
      duration: 3000,
      totalCost: 80,
      failedAt: 'node-2',
      error: 'Schema validation failed: missing required field "text"',
      nodes: [
        {
          id: 'node-1',
          name: 'Content Moderator',
          status: 'completed',
          duration: 1500,
          cost: 25,
          method: 'direct',
          confidence: 0.90
        },
        {
          id: 'node-2',
          name: 'Sentiment Analyzer',
          status: 'failed',
          duration: 1500,
          cost: 30,
          method: 'llm',
          error: 'Transform failed after 2 attempts'
        }
      ],
      input: { content: "Sample text for analysis" },
      output: null
    },
    {
      id: 'run-003',
      chainName: 'GAT Recommendation Pipeline',
      status: 'succeeded',
      startedAt: '2025-10-31T08:45:00Z',
      completedAt: '2025-10-31T08:45:05Z',
      duration: 5000,
      totalCost: 120,
      nodes: [
        {
          id: 'node-1',
          name: 'Text Formatter',
          status: 'completed',
          duration: 2000,
          cost: 15,
          method: 'gat',
          mappingUsed: 'GAT suggested: content -> text',
          confidence: 0.75
        },
        {
          id: 'node-2',
          name: 'Keyword Extractor',
          status: 'completed',
          duration: 3000,
          cost: 40,
          method: 'direct',
          confidence: 0.93
        }
      ],
      input: { content: "Advanced AI systems for enterprise" },
      output: {
        formatted: "Advanced AI Systems For Enterprise",
        keywords: ["AI", "systems", "enterprise", "advanced"],
        _provenance: {
          formatted: {
            origin: 'node-1',
            method: 'gat',
            confidence: 0.75,
            transformChain: ['node-1', 'gat_recommendation']
          },
          keywords: {
            origin: 'node-2',
            method: 'direct',
            confidence: 0.93,
            transformChain: ['node-2']
          }
        }
      }
    }
  ])
    } finally {
      setLoading(false)
    }
  }
  
  const [expandedRun, setExpandedRun] = useState(null)
  const [showProvenance, setShowProvenance] = useState(false)
  const [filterStatus, setFilterStatus] = useState('all')

  const getStatusIcon = (status) => {
    switch (status) {
      case 'succeeded':
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <RefreshCw className="h-4 w-4 text-yellow-500 animate-spin" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const getMethodBadge = (method) => {
    const badges = {
      'direct': { label: 'Direct', variant: 'success' },
      'deterministic': { label: 'Deterministic', variant: 'default' },
      'gat': { label: 'GAT', variant: 'warning' },
      'llm': { label: 'LLM', variant: 'destructive' }
    }
    return badges[method] || { label: method, variant: 'outline' }
  }

  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleString()
  }

  const filteredRuns = runs.filter(run => {
    if (filterStatus === 'all') return true
    return run.status === filterStatus
  })

  const ProvenanceViewer = ({ provenance, data }) => {
    if (!provenance || !data) return null

    return (
      <Card className="mt-4">
        <CardHeader>
          <CardTitle className="text-sm">Provenance Tracking</CardTitle>
          <CardDescription>Field-level lineage and confidence scores</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
              return (
                <div key={node.id} className="border rounded-lg p-3">
                  <div 
                    className="flex items-center space-x-3 cursor-pointer"
                    onClick={() => setExpandedNodes(prev => ({ ...prev, [nodeKey]: !prev[nodeKey] }))}
                  >
                    <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-xs font-medium">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(node.status)}
                          <span className="font-medium text-sm">{node.name}</span>
                          {node.method && (
                            <Badge variant={getMethodBadge(node.method).variant} className="text-xs">
                              {getMethodBadge(node.method).label}
                            </Badge>
                  {prov.transformChain && prov.transformChain.length > 1 && (
                    <div className="mt-2 flex items-center space-x-1">
                      {prov.transformChain.map((step, index) => (
                        <div key={index} className="flex items-center">
                          <Badge variant="secondary" className="text-xs">
                            {step}
                          </Badge>
                          {index < prov.transformChain.length - 1 && (
                            <ChevronRight className="h-3 w-3 mx-1" />
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    )
  }

  const RunCard = ({ run }) => {
    const isExpanded = expandedRun === run.id

    return (
      <Card>
        <CardHeader 
          className="cursor-pointer"
          onClick={() => setExpandedRun(isExpanded ? null : run.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {getStatusIcon(run.status)}
              <div>
                <CardTitle className="text-base">{run.chainName}</CardTitle>
                <CardDescription>
                  {formatDate(run.startedAt)} • {formatDuration(run.duration)}
                </CardDescription>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-sm font-medium">
                  ${(run.totalCost / 100).toFixed(2)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {run.nodes.length} nodes
                </p>
              </div>
              <Badge variant={run.status === 'succeeded' ? 'success' : run.status === 'failed' ? 'destructive' : 'default'}>
                {run.status}
              </Badge>
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </div>
          </div>
        </CardHeader>
        
        {isExpanded && (
          <CardContent>
            {/* Node Execution Timeline */}
            <div className="space-y-3 mb-4">
              <h4 className="font-medium text-sm">Execution Timeline</h4>
              {run.nodes.map((node, index) => {
                const nodeKey = `${run.id}-${node.id}`
                const isNodeExpanded = expandedNodes[nodeKey]
                
                return (
                  <div key={node.id} className="border rounded-lg p-3">
                    <div 
                      className="flex items-center space-x-3 cursor-pointer"
                      onClick={() => setExpandedNodes(prev => ({ ...prev, [nodeKey]: !prev[nodeKey] }))}
                    >
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-muted text-xs font-medium">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            {getStatusIcon(node.status)}
                            <span className="font-medium text-sm">{node.name}</span>
                            {node.method && (
                              <Badge variant={getMethodBadge(node.method).variant} className="text-xs">
                                {getMethodBadge(node.method).label}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center space-x-4 text-sm">
                            <span className="text-muted-foreground">
                              {formatDuration(node.duration)}
                            </span>
                            <span className="font-medium">
                              ${(node.cost / 100).toFixed(2)}
                            </span>
                            {node.confidence && (
                              <Badge variant="outline" className="text-xs">
                                {Math.round(node.confidence * 100)}%
                              </Badge>
                            )}
                            {isNodeExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          </div>
                        </div>
                        
                        {node.mappingUsed && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Mapping: {node.mappingUsed}
                          </p>
                        )}
                        
                        {node.error && (
                          <p className="text-xs text-red-500 mt-1">
                            Error: {node.error}
                          </p>
                        )}
                      </div>
                    </div>
                    
                    {/* Node Input/Output */}
                    {isNodeExpanded && (
                      <div className="mt-3 grid grid-cols-2 gap-3">
                        <div className="bg-muted/50 rounded-lg p-3">
                          <p className="text-xs font-medium mb-2 text-muted-foreground">Input</p>
                          <pre className="text-xs overflow-auto max-h-32">
                            {node.input ? JSON.stringify(node.input, null, 2) : 'No input data'}
                          </pre>
                        </div>
                        <div className="bg-muted/50 rounded-lg p-3">
                          <p className="text-xs font-medium mb-2 text-muted-foreground">Output</p>
                          <pre className="text-xs overflow-auto max-h-32">
                            {node.output ? JSON.stringify(node.output, null, 2) : 'No output data'}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
            
            {/* Input/Output */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Input</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                    {JSON.stringify(run.input, null, 2)}
                  </pre>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Output</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                    {run.output ? JSON.stringify(
                      Object.fromEntries(
                        Object.entries(run.output).filter(([k]) => k !== '_provenance')
                      ), null, 2
                    ) : 'null'}
                  </pre>
                </CardContent>
              </Card>
            </div>
            
            {/* Actions */}
            <div className="flex items-center justify-between">
              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowProvenance(!showProvenance)}
                >
                  <Eye className="h-4 w-4 mr-1" />
                  {showProvenance ? 'Hide' : 'View'} Provenance
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    const exportData = {
                      runId: run.id,
                      chainName: run.chainName,
                      status: run.status,
                      startedAt: run.startedAt,
                      completedAt: run.completedAt,
                      duration: run.duration,
                      totalCost: run.totalCost,
                      nodes: run.nodes,
                      input: run.input,
                      output: run.output,
                      provenance: run.output?._provenance
                    }
                    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `run-${run.id}-${Date.now()}.json`
                    a.click()
                    URL.revokeObjectURL(url)
                  }}
                >
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </Button>
              </div>
              
              {run.status === 'failed' && (
                <Button variant="default" size="sm">
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Retry
                </Button>
              )}
            </div>
            
            {/* Provenance Viewer */}
            {showProvenance && run.output && (
              <ProvenanceViewer 
                provenance={run.output._provenance} 
                data={run.output}
              />
            )}
          </CardContent>
        )}
      </Card>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Run History</h1>
          <p className="text-muted-foreground">
            Monitor chain executions, view provenance, and analyze performance
          </p>
        </div>
        <Button onClick={loadRuns} variant="outline" disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Loading...' : 'Refresh'}
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Runs</p>
                <p className="text-2xl font-bold">{runs.length}</p>
              </div>
              <PlayCircle className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Success Rate</p>
                <p className="text-2xl font-bold">
                  {Math.round((runs.filter(r => r.status === 'succeeded').length / runs.length) * 100)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Spent</p>
                <p className="text-2xl font-bold">
                  ${(runs.reduce((sum, r) => sum + r.totalCost, 0) / 100).toFixed(2)}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {formatDuration(runs.reduce((sum, r) => sum + r.duration, 0) / runs.length)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex space-x-2">
            <Button
              variant={filterStatus === 'all' ? 'default' : 'outline'}
              onClick={() => setFilterStatus('all')}
            >
              All
            </Button>
            <Button
              variant={filterStatus === 'succeeded' ? 'default' : 'outline'}
              onClick={() => setFilterStatus('succeeded')}
            >
              Succeeded
            </Button>
            <Button
              variant={filterStatus === 'failed' ? 'default' : 'outline'}
              onClick={() => setFilterStatus('failed')}
            >
              Failed
            </Button>
            <Button
              variant={filterStatus === 'running' ? 'default' : 'outline'}
              onClick={() => setFilterStatus('running')}
            >
              Running
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Run List */}
      <div className="space-y-4">
        {filteredRuns.map(run => (
          <RunCard key={run.id} run={run} />
        ))}
      </div>
    </div>
  )
}
