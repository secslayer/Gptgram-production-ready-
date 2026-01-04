import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Input } from '../components/ui/input'
import {
  DollarSign,
  CreditCard,
  Plus,
  Minus,
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  ExternalLink,
  RefreshCw
} from 'lucide-react'

export default function CompleteWallet() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [balance, setBalance] = useState(5000)
  const [transactions, setTransactions] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [topUpAmount, setTopUpAmount] = useState(1000)
  const [paymentStatus, setPaymentStatus] = useState(null)
  
  useEffect(() => {
    fetchWallet()
    checkPaymentStatus()
    
    // Handle Stripe redirects
    const path = window.location.pathname
    if (path.includes('/wallet/success')) {
      setPaymentStatus('success')
      window.history.replaceState({}, document.title, '/wallet')
      setTimeout(fetchWallet, 1000)
    } else if (path.includes('/wallet/cancel')) {
      setPaymentStatus('cancelled')
      window.history.replaceState({}, document.title, '/wallet')
    }
  }, [])
  
  const fetchWallet = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/wallet', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })
      setBalance(response.data.balance_cents)
    } catch (error) {
      console.error('Failed to fetch wallet:', error)
    }
  }
  
  const checkPaymentStatus = async () => {
    const sessionId = searchParams.get('session_id')
    if (sessionId) {
      setIsLoading(true)
      try {
        const response = await axios.get(
          `http://localhost:8000/api/wallet/verify-checkout?session_id=${sessionId}`
        )
        if (response.data.status === 'success') {
          setPaymentStatus('success')
          setBalance(response.data.balance)
          // Clear URL params
          window.history.replaceState({}, document.title, '/wallet')
        } else {
          setPaymentStatus('pending')
        }
      } catch (error) {
        setPaymentStatus('error')
      } finally {
        setIsLoading(false)
      }
    }
  }
  
  const handleStripeCheckout = async () => {
    setIsLoading(true)
    try {
      const response = await axios.post(
        'http://localhost:8000/api/wallet/create-checkout-session',
        {
          amount_cents: topUpAmount,
          currency: 'usd'
        },
        {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }
      )
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.url
    } catch (error) {
      console.error('Failed to create checkout session:', error)
      setPaymentStatus('error')
    } finally {
      setIsLoading(false)
    }
  }
  
  
  // Mock transaction history
  const mockTransactions = [
    {
      id: '1',
      type: 'credit',
      amount: 1000,
      description: 'Wallet Top-Up',
      date: '2025-10-31T10:30:00Z',
      status: 'completed'
    },
    {
      id: '2',
      type: 'debit',
      amount: 155,
      description: 'Chain: Text Processing Pipeline',
      date: '2025-10-31T10:35:00Z',
      status: 'completed'
    },
    {
      id: '3',
      type: 'debit',
      amount: 80,
      description: 'Chain: Sentiment Analysis',
      date: '2025-10-30T15:20:00Z',
      status: 'completed'
    },
    {
      id: '4',
      type: 'credit',
      amount: 500,
      description: 'Refund: Failed Chain',
      date: '2025-10-30T14:00:00Z',
      status: 'completed'
    }
  ]
  
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-16 w-16 text-green-500" />
      case 'error':
        return <XCircle className="h-16 w-16 text-red-500" />
      case 'pending':
        return <Clock className="h-16 w-16 text-yellow-500" />
      default:
        return null
    }
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Wallet</h1>
        <p className="text-muted-foreground">
          Manage your funds and view transaction history
        </p>
      </div>
      
      {/* Payment Status Alert */}
      {paymentStatus && (
        <Card className={`border-2 ${
          paymentStatus === 'success' ? 'border-green-500 bg-green-50' :
          paymentStatus === 'error' ? 'border-red-500 bg-red-50' :
          'border-yellow-500 bg-yellow-50'
        }`}>
          <CardContent className="p-6">
            <div className="flex items-center space-x-4">
              {getStatusIcon(paymentStatus)}
              <div className="flex-1">
                <h3 className="text-lg font-semibold">
                  {paymentStatus === 'success' ? 'Payment Successful!' :
                   paymentStatus === 'error' ? 'Payment Failed' :
                   'Payment Processing...'}
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {paymentStatus === 'success' ? 'Your wallet has been topped up successfully.' :
                   paymentStatus === 'error' ? 'There was an issue processing your payment. Please try again.' :
                   'Your payment is being processed. Please wait...'}
                </p>
              </div>
              {paymentStatus !== 'pending' && (
                <Button
                  variant="outline"
                  onClick={() => setPaymentStatus(null)}
                >
                  Dismiss
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}
      
      <div className="grid gap-6 md:grid-cols-2">
        {/* Balance Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Current Balance
              <DollarSign className="h-5 w-5 text-muted-foreground" />
            </CardTitle>
            <CardDescription>
              Available funds for chain execution
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">
              ${(balance / 100).toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              USD • Updated just now
            </p>
            
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span>Reserved (holds)</span>
                <span className="font-medium">$0.00</span>
              </div>
              <div className="flex justify-between text-sm">
                <span>Available</span>
                <span className="font-medium text-green-600">
                  ${(balance / 100).toFixed(2)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Top Up Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Top Up Wallet
              <CreditCard className="h-5 w-5 text-muted-foreground" />
            </CardTitle>
            <CardDescription>
              Add funds using Stripe (test mode)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Amount (USD)</label>
                <div className="flex items-center space-x-2 mt-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setTopUpAmount(Math.max(100, topUpAmount - 100))}
                  >
                    <Minus className="h-4 w-4" />
                  </Button>
                  <Input
                    type="number"
                    value={topUpAmount / 100}
                    onChange={(e) => setTopUpAmount(Math.round(e.target.value * 100))}
                    className="text-center"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setTopUpAmount(topUpAmount + 100)}
                  >
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              
              <div className="flex space-x-2">
                {[500, 1000, 2000, 5000].map(amount => (
                  <Button
                    key={amount}
                    variant={topUpAmount === amount ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setTopUpAmount(amount)}
                  >
                    ${amount / 100}
                  </Button>
                ))}
              </div>
              
              <div className="space-y-2">
                <Button
                  className="w-full"
                  onClick={handleStripeCheckout}
                  disabled={isLoading || topUpAmount < 100}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <CreditCard className="h-4 w-4 mr-2" />
                      Pay with Stripe
                    </>
                  )}
                </Button>
              </div>
              
              <div className="text-xs text-muted-foreground">
                <p>• Test card: 4242 4242 4242 4242</p>
                <p>• Any future expiry and CVC</p>
                <p>• Powered by Stripe (test mode)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Transaction History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Transaction History
            <Button variant="outline" size="sm" onClick={fetchWallet}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </CardTitle>
          <CardDescription>
            Recent wallet activity and chain executions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockTransactions.map(tx => (
              <div
                key={tx.id}
                className="flex items-center justify-between p-4 border rounded-lg"
              >
                <div className="flex items-center space-x-4">
                  {tx.type === 'credit' ? (
                    <div className="p-2 bg-green-100 rounded-full">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    </div>
                  ) : (
                    <div className="p-2 bg-red-100 rounded-full">
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    </div>
                  )}
                  <div>
                    <p className="font-medium">{tx.description}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(tx.date).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-semibold ${
                    tx.type === 'credit' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {tx.type === 'credit' ? '+' : '-'}${(tx.amount / 100).toFixed(2)}
                  </p>
                  <Badge variant={tx.status === 'completed' ? 'success' : 'default'}>
                    {tx.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      {/* Stripe Connect Card (Creator Payouts) */}
      <Card>
        <CardHeader>
          <CardTitle>Creator Payouts</CardTitle>
          <CardDescription>
            Enable Stripe Connect to receive payments for your agents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">
                Connect your Stripe account to receive automatic payouts when
                other users execute chains with your verified agents.
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Platform fee: 10% • Payout schedule: Weekly
              </p>
            </div>
            <Button variant="outline">
              <ExternalLink className="h-4 w-4 mr-2" />
              Connect Stripe
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
