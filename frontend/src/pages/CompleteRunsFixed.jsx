import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { 
  PlayCircle,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronRight,
  ChevronDown,
  RefreshCw,
  Timer,
  GitBranch,
  Eye,
  EyeOff,
  Filter
} from 'lucide-react'

export default function CompleteRuns() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedRun, setExpandedRun] = useState(null)
  const [expandedNodes, setExpandedNodes] = useState({})
  const [filterStatus, setFilterStatus] = useState('all')
  const [showProvenance, setShowProvenance] = useState(false)

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
      setLoading(false)
    } catch (error) {
      console.error('Failed to load runs:', error)
      setLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'succeeded':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />
      case 'running':
        return <PlayCircle className="h-4 w-4 text-yellow-600 animate-pulse" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />
    }
  }

  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'None') {
      return 'N/A'
    }
    try {
      return new Date(dateStr).toLocaleString()
    } catch {
      return 'Invalid date'
    }
  }

  const filteredRuns = runs.filter(run => {
    if (filterStatus === 'all') return true
    return run.status === filterStatus
  })

  const RunCard = ({ run }) => {
    const isExpanded = expandedRun === run.id

    return (
      <Card className="overflow-hidden">
        <CardHeader 
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => setExpandedRun(isExpanded ? null : run.id)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon(run.status)}
              <div>
                <CardTitle className="text-lg">{run.chainName}</CardTitle>
                <CardDescription className="text-sm">
                  Run ID: {run.runId.substring(0, 8)}...
                </CardDescription>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant={run.status === 'succeeded' ? 'success' : run.status === 'failed' ? 'destructive' : 'default'}>
                {run.status}
              </Badge>
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </div>
          </div>
        </CardHeader>

        {isExpanded && (
          <>
            {/* Timeline */}
            <div className="px-6 py-4 bg-muted/30 border-y">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-6">
                  <div className="flex items-center space-x-2">
                    <Clock className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Started:</span>
                    <span className="font-medium">{formatDate(run.startedAt)}</span>
                  </div>
                  {run.completedAt && (
                    <div className="flex items-center space-x-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-muted-foreground">Completed:</span>
                      <span className="font-medium">{formatDate(run.completedAt)}</span>
                    </div>
                  )}
                </div>
                {run.duration > 0 && (
                  <div className="flex items-center space-x-2">
                    <Timer className="h-4 w-4 text-muted-foreground" />
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="font-medium">{formatDuration(run.duration)}</span>
                  </div>
                )}
              </div>
            </div>

            <CardContent className="pt-6">
              {/* Outputs */}
              {run.output && Object.keys(run.output).length > 0 && (
                <div className="space-y-4">
                  <h4 className="font-medium text-sm">Node Outputs</h4>
                  {Object.entries(run.output).map(([nodeId, output]) => (
                    <div key={nodeId} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">{nodeId}</span>
                        <Badge variant="outline" className="text-xs">
                          {output.type || 'node'}
                        </Badge>
                      </div>
                      <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(output, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              )}

              {/* Error */}
              {run.error && (
                <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">Error: {run.error}</p>
                </div>
              )}

              {/* Cost */}
              {run.totalCost > 0 && (
                <div className="mt-4 flex items-center justify-end">
                  <div className="text-sm text-muted-foreground">Total Cost:</div>
                  <div className="ml-2 text-lg font-bold">${(run.totalCost / 100).toFixed(2)}</div>
                </div>
              )}
            </CardContent>
          </>
        )}
      </Card>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Run History</h1>
          <p className="text-muted-foreground">
            View and analyze your chain execution history
          </p>
        </div>
        <Button onClick={loadRuns} disabled={loading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <div className="flex space-x-2">
              <Button
                size="sm"
                variant={filterStatus === 'all' ? 'default' : 'outline'}
                onClick={() => setFilterStatus('all')}
              >
                All ({runs.length})
              </Button>
              <Button
                size="sm"
                variant={filterStatus === 'succeeded' ? 'default' : 'outline'}
                onClick={() => setFilterStatus('succeeded')}
              >
                Succeeded ({runs.filter(r => r.status === 'succeeded').length})
              </Button>
              <Button
                size="sm"
                variant={filterStatus === 'failed' ? 'default' : 'outline'}
                onClick={() => setFilterStatus('failed')}
              >
                Failed ({runs.filter(r => r.status === 'failed').length})
              </Button>
              <Button
                size="sm"
                variant={filterStatus === 'running' ? 'default' : 'outline'}
                onClick={() => setFilterStatus('running')}
              >
                Running ({runs.filter(r => r.status === 'running').length})
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Run List */}
      {loading ? (
        <div className="text-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
          <p className="mt-2 text-muted-foreground">Loading runs...</p>
        </div>
      ) : filteredRuns.length > 0 ? (
        <div className="space-y-4">
          {filteredRuns.map(run => (
            <RunCard key={run.id} run={run} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <GitBranch className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              {filterStatus === 'all' ? 'No runs found. Execute a chain to see it here.' : `No ${filterStatus} runs found.`}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
