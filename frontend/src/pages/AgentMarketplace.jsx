import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
// Tabs component removed - using custom implementation
import {
  Search,
  Filter,
  Bot,
  Zap,
  TrendingUp,
  DollarSign,
  Star,
  Download,
  ShoppingCart,
  Plus,
  Eye,
  Clock,
  CheckCircle,
  AlertCircle,
  Sparkles
} from 'lucide-react'
import axios from 'axios'

export default function AgentMarketplace() {
  const [agents, setAgents] = useState([])
  const [featuredAgents, setFeaturedAgents] = useState([])
  const [categories, setCategories] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [sortBy, setSortBy] = useState('popular')
  const [loading, setLoading] = useState(true)
  const [cartItems, setCartItems] = useState([])

  useEffect(() => {
    loadMarketplace()
  }, [])

  const loadMarketplace = async () => {
    try {
      // Load all agents
      const response = await axios.get('http://localhost:8000/api/agents')
      const allAgents = response.data || []
      
      // Categorize agents
      const agentsByCategory = {}
      allAgents.forEach(agent => {
        const category = agent.category || agent.type || 'general'
        if (!agentsByCategory[category]) {
          agentsByCategory[category] = []
        }
        agentsByCategory[category].push({
          ...agent,
          rating: 4.5 + Math.random() * 0.5,
          downloads: Math.floor(Math.random() * 1000) + 100,
          reviews: Math.floor(Math.random() * 50) + 10
        })
      })
      
      // Extract unique categories
      const uniqueCategories = Object.keys(agentsByCategory)
      setCategories(['all', ...uniqueCategories])
      
      // Set featured agents (LLM-powered or high verification)
      const featured = allAgents.filter(a => 
        a.type === 'llm' || 
        a.verification_level === 'L3' ||
        a.price_cents > 75
      ).slice(0, 4)
      
      setFeaturedAgents(featured)
      setAgents(allAgents)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load marketplace:', error)
      setLoading(false)
    }
  }

  const installAgent = async (agent) => {
    try {
      // In a real app, this would add the agent to user's workspace
      alert(`Installing ${agent.name}...`)
      
      // Add to cart for tracking
      setCartItems([...cartItems, agent.id])
      
      // Refresh agents in the system
      window.location.reload()
    } catch (error) {
      console.error('Failed to install agent:', error)
    }
  }

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = !searchQuery || 
      agent.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description?.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesCategory = selectedCategory === 'all' || 
      agent.category === selectedCategory ||
      agent.type === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  // Sort agents
  const sortedAgents = [...filteredAgents].sort((a, b) => {
    switch(sortBy) {
      case 'price_low':
        return (a.price_cents || 0) - (b.price_cents || 0)
      case 'price_high':
        return (b.price_cents || 0) - (a.price_cents || 0)
      case 'rating':
        return (b.rating || 0) - (a.rating || 0)
      case 'popular':
      default:
        return (b.downloads || 0) - (a.downloads || 0)
    }
  })

  const AgentCard = ({ agent, featured = false }) => (
    <Card className={`hover:shadow-lg transition-all ${featured ? 'border-primary' : ''}`}>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div className="flex items-center space-x-2">
            <div className={`w-10 h-10 rounded-lg ${
              agent.type === 'llm' ? 'bg-purple-100' :
              agent.type === 'n8n' ? 'bg-blue-100' :
              'bg-gray-100'
            } flex items-center justify-center`}>
              {agent.type === 'llm' ? 
                <Sparkles className="h-5 w-5 text-purple-600" /> :
                <Bot className="h-5 w-5 text-blue-600" />
              }
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <div className="flex items-center space-x-2 mt-1">
                <Badge variant="secondary">{agent.type || 'custom'}</Badge>
                <Badge variant={
                  agent.verification_level === 'L3' ? 'default' :
                  agent.verification_level === 'L2' ? 'secondary' :
                  'outline'
                }>
                  {agent.verification_level || 'L1'}
                </Badge>
              </div>
            </div>
          </div>
          {featured && (
            <Badge variant="default" className="bg-yellow-500">
              <Star className="h-3 w-3 mr-1" />
              Featured
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <CardDescription className="line-clamp-2">
          {agent.description || 'A powerful agent for your workflows'}
        </CardDescription>
        
        {/* Stats */}
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-3">
            <div className="flex items-center">
              <Star className="h-4 w-4 text-yellow-500 mr-1" />
              <span>{agent.rating?.toFixed(1) || '4.5'}</span>
            </div>
            <div className="flex items-center text-muted-foreground">
              <Download className="h-4 w-4 mr-1" />
              <span>{agent.downloads || 0}</span>
            </div>
            <div className="flex items-center text-muted-foreground">
              <Eye className="h-4 w-4 mr-1" />
              <span>{agent.reviews || 0}</span>
            </div>
          </div>
        </div>
        
        {/* Category */}
        {agent.category && (
          <div className="flex items-center space-x-2">
            <span className="text-xs text-muted-foreground">Category:</span>
            <Badge variant="outline" className="text-xs">
              {agent.category}
            </Badge>
          </div>
        )}
        
        {/* Price and Actions */}
        <div className="flex items-center justify-between pt-2 border-t">
          <div className="flex items-center space-x-2">
            <DollarSign className="h-4 w-4 text-green-600" />
            <span className="text-lg font-bold">
              ${((agent.price_cents || 0) / 100).toFixed(2)}
            </span>
            <span className="text-xs text-muted-foreground">per run</span>
          </div>
          <div className="flex space-x-2">
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => window.open(`/agents/${agent.id}`, '_blank')}
            >
              <Eye className="h-4 w-4 mr-1" />
              View
            </Button>
            <Button 
              size="sm"
              onClick={() => installAgent(agent)}
              disabled={cartItems.includes(agent.id)}
            >
              {cartItems.includes(agent.id) ? (
                <>
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Installed
                </>
              ) : (
                <>
                  <ShoppingCart className="h-4 w-4 mr-1" />
                  Install
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <Bot className="h-12 w-12 text-muted-foreground animate-pulse mx-auto mb-4" />
          <p>Loading marketplace...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Agent Marketplace</h1>
        <p className="text-muted-foreground">
          Discover, install, and deploy pre-built agents for your workflows
        </p>
      </div>

      {/* Featured Agents */}
      {featuredAgents.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold flex items-center">
            <Sparkles className="h-5 w-5 mr-2 text-yellow-500" />
            Featured Agents
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {featuredAgents.map(agent => (
              <AgentCard key={agent.id} agent={agent} featured={true} />
            ))}
          </div>
        </div>
      )}

      {/* Search and Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
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
            
            <select 
              className="px-3 py-2 border rounded-lg"
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
            
            <select 
              className="px-3 py-2 border rounded-lg"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="popular">Most Popular</option>
              <option value="rating">Highest Rated</option>
              <option value="price_low">Price: Low to High</option>
              <option value="price_high">Price: High to Low</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Agent Grid */}
      <div className="space-y-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold">All Agents ({sortedAgents.length})</h2>
          <Badge variant="secondary">
            <TrendingUp className="h-3 w-3 mr-1" />
            Trending
          </Badge>
        </div>
        
        {sortedAgents.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedAgents.map(agent => (
              <AgentCard key={agent.id} agent={agent} />
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="p-12 text-center">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No agents found matching your criteria</p>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Marketplace Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Agents</p>
              <p className="text-2xl font-bold">{agents.length}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Categories</p>
              <p className="text-2xl font-bold">{categories.length - 1}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Avg Price</p>
              <p className="text-2xl font-bold">
                ${(agents.reduce((sum, a) => sum + (a.price_cents || 0), 0) / agents.length / 100).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Verified</p>
              <p className="text-2xl font-bold">
                {agents.filter(a => a.verification_level === 'L3').length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
