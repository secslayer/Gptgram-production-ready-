import { Routes, Route, Navigate, Link, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { LayoutDashboard, Wallet, Bot, GitBranch, Play, TrendingUp, Code, Zap, ShoppingBag } from 'lucide-react'

// Import all complete pages
import CompleteLogin from './pages/CompleteLogin'
import CompleteDashboard from './pages/CompleteDashboard'
import CompleteAgents from './pages/CompleteAgents'
import AgentCreationFixed from './pages/AgentCreationFixed'
import EnhancedChainBuilder from './pages/EnhancedChainBuilder'
import ChainBuilderFixed from './pages/ChainBuilderFixed'
import CompleteRunsFixed from './pages/CompleteRunsFixed'
import RealAnalytics from './pages/RealAnalytics'
import CompleteWallet from './pages/CompleteWallet'
import CodeFuserWorking from './pages/CodeFuserWorking'
import AgentManager from './pages/AgentManager'
import AgentMarketplace from './pages/AgentMarketplace'

// Layout component with navigation
function Layout({ children }) {
  const location = useLocation()
  const [user, setUser] = useState(null)

  useEffect(() => {
    // Check for token and get user info
    const token = localStorage.getItem('token')
    const username = localStorage.getItem('username') || 'demo'
    if (token) {
      setUser({ username: username, email: `${username}@gptgram.ai` })
    }
  }, [])

  const navItems = [
    { path: '/', label: 'Dashboard', icon: 'LayoutDashboard' },
    { path: '/marketplace', label: 'Marketplace', icon: 'ShoppingBag' },
    { path: '/agents', label: 'My Agents', icon: 'Zap' },
    { path: '/chains', label: 'Chain Builder', icon: 'GitBranch' },
    { path: '/runs', label: 'Run History', icon: 'Play' },
    { path: '/analytics', label: 'Analytics', icon: 'TrendingUp' },
    { path: '/code-fuser', label: 'Code Fuser', icon: 'Code' },
    { path: '/wallet', label: 'Wallet', icon: 'Wallet' }
  ]

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    window.location.href = '/login'
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 w-64 h-full bg-card border-r">
        <div className="p-4 border-b">
          <h1 className="text-xl font-bold">GPTGram</h1>
          <p className="text-sm text-muted-foreground">A2A DAG Orchestration</p>
        </div>
        
        <nav className="p-4 space-y-2">
          {navItems.map(item => {
            const IconComponent = {
              LayoutDashboard,
              Wallet,
              Bot,
              Zap,
              GitBranch,
              Play,
              TrendingUp,
              Code,
              ShoppingBag
            }[item.icon]
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  location.pathname === item.path
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
              >
                {IconComponent && <IconComponent className="h-5 w-5" />}
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
        
        {user && (
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t">
            <div className="mb-3">
              <p className="text-sm font-medium">{user.username}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="w-full px-3 py-2 text-sm bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90"
            >
              Logout
            </button>
          </div>
        )}
      </div>
      
      {/* Main content */}
      <div className="ml-64">
        {children}
      </div>
    </div>
  )
}

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  return <Layout>{children}</Layout>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<CompleteLogin />} />
      <Route path="/register" element={<CompleteLogin />} />
      
      <Route path="/" element={
        <ProtectedRoute>
          <CompleteDashboard />
        </ProtectedRoute>
      } />
      
      <Route path="/marketplace" element={
        <ProtectedRoute>
          <AgentMarketplace />
        </ProtectedRoute>
      } />
      
      <Route path="/agents" element={
        <ProtectedRoute>
          <AgentManager />
        </ProtectedRoute>
      } />
      
      <Route path="/agents/create" element={
        <ProtectedRoute>
          <AgentCreationFixed />
        </ProtectedRoute>
      } />
      
      <Route path="/chains" element={
        <ProtectedRoute>
          <ChainBuilderFixed />
        </ProtectedRoute>
      } />
      
      <Route path="/runs" element={
        <ProtectedRoute>
          <CompleteRunsFixed />
        </ProtectedRoute>
      } />
      
      <Route path="/analytics" element={
        <ProtectedRoute>
          <RealAnalytics />
        </ProtectedRoute>
      } />
      
      <Route path="/wallet" element={
        <ProtectedRoute>
          <CompleteWallet />
        </ProtectedRoute>
      } />
      
      <Route path="/wallet/success" element={
        <ProtectedRoute>
          <CompleteWallet />
        </ProtectedRoute>
      } />
      
      <Route path="/wallet/cancel" element={
        <ProtectedRoute>
          <CompleteWallet />
        </ProtectedRoute>
      } />
      
      <Route path="/code-fuser" element={
        <ProtectedRoute>
          <CodeFuserWorking />
        </ProtectedRoute>
      } />
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

// Simple Register Page
function RegisterPage() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-4">Register for GPTGram</h1>
        <form>
          <div className="mb-4">
            <input 
              type="email" 
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Email"
            />
          </div>
          <div className="mb-4">
            <input 
              type="text" 
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Username"
            />
          </div>
          <div className="mb-4">
            <input 
              type="password"
              className="w-full px-3 py-2 border rounded-lg"
              placeholder="Password"
            />
          </div>
          <button 
            type="submit"
            className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600"
          >
            Sign Up
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          Already have an account? <a href="/login" className="text-blue-500">Sign In</a>
        </p>
      </div>
    </div>
  )
}

export default App
