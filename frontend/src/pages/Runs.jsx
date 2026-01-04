import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  PlayCircle, 
  Clock,
  DollarSign,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Eye,
  ChevronDown,
  ChevronUp,
  GitBranch,
  FileJson
} from 'lucide-react'
import axios from 'axios'

export default function Runs() {
  const [runs, setRuns] = useState([])
  const [expandedRun, setExpandedRun] = useState(null)
  const [selectedRun, setSelectedRun] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    fetchRuns()
  }, [])

  const fetchRuns = async () => {
    setIsLoading(true)
    try {
      const response = await axios.get('/api/chains/runs')
      setRuns(response.data)
    } catch (error) {
      console.error('Failed to fetch runs:', error)
      // Use demo data
      setRuns([
        {
          run_id: '1',
          chain_name: 'Text Processing Pipeline',
          status: 'succeeded',
          started_at: '2025-10-31T10:30:00',
          finished_at: '2025-10-31T10:30:03',
          spent_cents: 155,
          nodes_executed: 3,
          final_output: {
            summary: 'AI is transforming industries at an unprecedented pace.',
            sentiment: 'positive',
            translation: 'L\'IA transforme les industries à un rythme sans précédent.'
          },
          provenance_map: {
            summary: {
              origin: 'node_1',
              method: 'direct',
              confidence: 0.95,
              transform_chain: ['node_1']
            },
            sentiment: {
              origin: 'node_2',
              method: 'direct',
              confidence: 0.98,
              transform_chain: ['node_2']
            },
            translation: {
              origin: 'node_3',
              method: 'transformed',
              confidence: 0.92,
              transform_chain: ['node_3', 'mapping_hint']
            }
          }
        },
        {
          run_id: '2',
          chain_name: 'Content Analysis',
          status: 'running',
          started_at: '2025-10-31T10:35:00',
          spent_cents: 80,
          nodes_executed: 2
        },
        {
          run_id: '3',
          chain_name: 'Document Summarizer',
          status: 'failed',
          started_at: '2025-10-31T10:25:00',
          finished_at: '2025-10-31T10:25:05',
          spent_cents: 45,
          nodes_executed: 1,
          error: 'Agent timeout on node_2'
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (status) => {
    switch(status) {
      case 'succeeded':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'running':
        return <AlertCircle className="h-4 w-4 text-yellow-500 animate-pulse" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status) => {
    switch(status) {
      case 'succeeded':
        return <Badge className="bg-green-500">Succeeded</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      case 'running':
        return <Badge className="bg-yellow-500">Running</Badge>
      default:
        return <Badge variant="secondary">Pending</Badge>
    }
  }

  const formatDuration = (start, end) => {
    if (!start || !end) return 'N/A'
    const startTime = new Date(start)
    const endTime = new Date(end)
    const duration = (endTime - startTime) / 1000
    return `${duration.toFixed(1)}s`
  }

  const ProvenanceViewer = ({ provenance }) => {
    if (!provenance) return null

    return (
      <div className="space-y-3">
        <h4 className="font-semibold text-sm">Field Provenance</h4>
        {Object.entries(provenance).map(([field, data]) => (
          <div key={field} className="border rounded p-3 space-y-2">
            <div className="flex justify-between items-start">
              <span className="font-medium text-sm">{field}</span>
              <Badge variant="outline" className="text-xs">
                {(data.confidence * 100).toFixed(0)}% confidence
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <div>Origin: {data.origin}</div>
              <div>Method: {data.method}</div>
              <div>Transform Chain: {data.transform_chain.join(' → ')}</div>
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Chain Runs</h1>
        <p className="text-muted-foreground">
          View execution history and provenance tracking
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Runs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{runs.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Success Rate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {runs.length > 0 
                ? `${((runs.filter(r => r.status === 'succeeded').length / runs.length) * 100).toFixed(0)}%`
                : '0%'
              }
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active Runs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {runs.filter(r => r.status === 'running').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Spent</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ${(runs.reduce((sum, r) => sum + (r.spent_cents || 0), 0) / 100).toFixed(2)}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Runs List */}
      <Card>
        <CardHeader>
          <CardTitle>Execution History</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">Loading runs...</div>
          ) : (
            <div className="space-y-2">
              {runs.map(run => (
                <div key={run.run_id} className="border rounded-lg">
                  <div 
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => setExpandedRun(expandedRun === run.run_id ? null : run.run_id)}
                  >
                    <div className="flex items-center space-x-4">
                      {getStatusIcon(run.status)}
                      <div>
                        <p className="font-medium">{run.chain_name}</p>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {new Date(run.started_at).toLocaleString()}
                          </span>
                          <span className="flex items-center">
                            <GitBranch className="h-3 w-3 mr-1" />
                            {run.nodes_executed || 0} nodes
                          </span>
                          <span className="flex items-center">
                            <DollarSign className="h-3 w-3 mr-1" />
                            ${(run.spent_cents / 100).toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {getStatusBadge(run.status)}
                      <Button variant="ghost" size="sm">
                        {expandedRun === run.run_id ? 
                          <ChevronUp className="h-4 w-4" /> : 
                          <ChevronDown className="h-4 w-4" />
                        }
                      </Button>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedRun === run.run_id && (
                    <div className="px-4 pb-4 border-t">
                      <div className="pt-4 grid grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold text-sm mb-2">Execution Details</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Run ID:</span>
                              <code className="text-xs">{run.run_id}</code>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Duration:</span>
                              <span>{formatDuration(run.started_at, run.finished_at)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-muted-foreground">Total Cost:</span>
                              <span>${(run.spent_cents / 100).toFixed(2)}</span>
                            </div>
                          </div>

                          {run.error && (
                            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                              Error: {run.error}
                            </div>
                          )}
                        </div>

                        <div>
                          {run.final_output && (
                            <>
                              <h4 className="font-semibold text-sm mb-2">Output</h4>
                              <div className="bg-muted p-2 rounded text-xs overflow-auto max-h-32">
                                <pre>{JSON.stringify(run.final_output, null, 2)}</pre>
                              </div>
                            </>
                          )}
                        </div>
                      </div>

                      {run.provenance_map && (
                        <div className="mt-4">
                          <ProvenanceViewer provenance={run.provenance_map} />
                        </div>
                      )}

                      <div className="mt-4 flex space-x-2">
                        <Button size="sm" variant="outline">
                          <Eye className="h-3 w-3 mr-1" />
                          View Full Trace
                        </Button>
                        <Button size="sm" variant="outline">
                          <FileJson className="h-3 w-3 mr-1" />
                          Export Provenance
                        </Button>
                        {run.status === 'running' && (
                          <Button size="sm" variant="destructive">
                            Cancel Run
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
