'use client'

import { useState, useEffect, useCallback } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
// import { Dialog } from '@/components/ui/dialog'
import { Wallet, Zap, Settings, File, Plus, X, Globe, Activity, Gem } from 'lucide-react'

interface WalletData {
  id: string
  name: string
  address: string
  network: string
  isFamous: boolean
  source: string
  note: string | null
  active: boolean
}

interface AlertData {
  id: string
  whaleName: string
  whaleAddress: string
  network: string
  tokenSymbol: string
  tokenName: string
  tokenAddress: string
  buyAmount: number
  buyAmountUsd: number
  tokenPrice: number
  marketCap: number
  liquidity: number
  volume24h: number
  timestamp: string
  txHash: string | null
  isGem: boolean
}

interface Stats {
  totalWallets: number
  famousWallets: number
  solanaWallets: number
  ethWallets: number
  totalAlerts: number
  gemAlerts: number
}

export default function Home() {
  const [wallets, setWallets] = useState<WalletData[]>([])
  const [alerts, setAlerts] = useState<AlertData[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  // Add wallet form
  const [newName, setNewName] = useState('')
  const [newAddress, setNewAddress] = useState('')
  const [newNetwork, setNewNetwork] = useState('solana')
  const [newFamous, setNewFamous] = useState(false)

  // Settings
  const [minBuy, setMinBuy] = useState('50')
  const [maxBuy, setMaxBuy] = useState('2000000')
  const [onlyFamous, setOnlyFamous] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/data')
      const data = await res.json()
      setWallets(data.wallets || [])
      setAlerts(data.alerts || [])
      setStats(data.stats || null)
    } catch (e) {
      console.error('Fetch error:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  const addWallet = async () => {
    if (!newName || !newAddress) return
    await fetch('/api/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'addWallet',
        name: newName,
        address: newAddress,
        network: newNetwork,
        isFamous: newFamous,
      })
    })
    setNewName('')
    setNewAddress('')
    setNewFamous(false)
    fetchData()
  }

  const removeWallet = async (address: string) => {
    await fetch('/api/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'removeWallet', address })
    })
    fetchData()
  }

  const seedWallets = async () => {
    await fetch('/api/data', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'seedWallets' })
    })
    fetchData()
  }

  const formatUsd = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`
    if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}K`
    if (val > 0) return `$${val.toFixed(4)}`
    return '?'
  }

  const networkIcon = (network: string) => {
    return network === 'solana' ? '🟢' : network === 'ethereum' ? '🟣' : '🟡'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Wallet className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Whale Tracker</h1>
              <p className="text-xs text-slate-400">Dashboard & Management</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="border-green-500/50 text-green-400">
              <Activity className="w-3 h-3 mr-1" />
              {stats?.totalWallets || 0} Wallets
            </Badge>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="grid w-full grid-cols-2 md:grid-cols-5 mb-6 bg-slate-900 border border-slate-800">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Activity className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="alerts" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Zap className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Alerts</span>
            </TabsTrigger>
            <TabsTrigger value="wallets" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Wallet className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Wallets</span>
            </TabsTrigger>
            <TabsTrigger value="files" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <File className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Files</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Settings className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Wallet className="w-5 h-5 text-amber-500" />
                    <Badge variant="secondary" className="bg-amber-500/10 text-amber-400 text-xs">Total</Badge>
                  </div>
                  <p className="text-3xl font-bold">{stats?.totalWallets || 0}</p>
                  <p className="text-xs text-slate-400">Tracked Wallets</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Gem className="w-5 h-5 text-purple-500" />
                    <Badge variant="secondary" className="bg-purple-500/10 text-purple-400 text-xs">Famous</Badge>
                  </div>
                  <p className="text-3xl font-bold">{stats?.famousWallets || 0}</p>
                  <p className="text-xs text-slate-400">Famous Devs</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Zap className="w-5 h-5 text-yellow-500" />
                    <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-400 text-xs">Alerts</Badge>
                  </div>
                  <p className="text-3xl font-bold">{stats?.totalAlerts || 0}</p>
                  <p className="text-xs text-slate-400">Buy Alerts</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Gem className="w-5 h-5 text-pink-500" />
                    <Badge variant="secondary" className="bg-pink-500/10 text-pink-400 text-xs">Gems</Badge>
                  </div>
                  <p className="text-3xl font-bold">{stats?.gemAlerts || 0}</p>
                  <p className="text-xs text-slate-400">GEM Alerts</p>
                </CardContent>
              </Card>
            </div>

            {/* Network Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <span className="text-xl">🟢</span> Solana Network
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-green-400">{stats?.solanaWallets || 0}</p>
                  <p className="text-xs text-slate-400">Wallets tracked</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <span className="text-xl">🟣</span> Ethereum Network
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold text-purple-400">{stats?.ethWallets || 0}</p>
                  <p className="text-xs text-slate-400">Wallets tracked</p>
                </CardContent>
              </Card>
            </div>

            {/* Recent Alerts */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="w-5 h-5 text-amber-500" />
                  Recent Whale Activity
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-slate-400 text-sm">Loading...</p>
                ) : alerts.length === 0 ? (
                  <p className="text-slate-400 text-sm">No alerts yet. Alerts will appear here when whales buy.</p>
                ) : (
                  <ScrollArea className="h-96">
                    <div className="space-y-2">
                      {alerts.slice(0, 20).map((alert) => (
                        <div key={alert.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors">
                          <div className="flex items-center gap-3">
                            {alert.isGem && <Gem className="w-4 h-4 text-pink-500" />}
                            <div>
                              <p className="text-sm font-medium">{alert.whaleName}</p>
                              <p className="text-xs text-slate-400">
                                {networkIcon(alert.network)} {alert.tokenSymbol} - {alert.tokenName}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-bold text-amber-400">{formatUsd(alert.buyAmountUsd)}</p>
                            <p className="text-xs text-slate-400">MC: {formatUsd(alert.marketCap)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Alerts Tab */}
          <TabsContent value="alerts" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  All Buy Alerts
                </CardTitle>
              </CardHeader>
              <CardContent>
                {alerts.length === 0 ? (
                  <div className="text-center py-12">
                    <Zap className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400">No alerts yet</p>
                    <p className="text-xs text-slate-500 mt-1">Alerts will appear here when whales buy tokens</p>
                  </div>
                ) : (
                  <ScrollArea className="h-[600px]">
                    <div className="space-y-3">
                      {alerts.map((alert) => (
                        <div key={alert.id} className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              {alert.isGem && <Badge className="bg-pink-500/20 text-pink-400 border-pink-500/30"><Gem className="w-3 h-3 mr-1" />GEM</Badge>}
                              <Badge variant="outline" className={alert.network === 'solana' ? 'border-green-500/30 text-green-400' : 'border-purple-500/30 text-purple-400'}>
                                {networkIcon(alert.network)} {alert.network}
                              </Badge>
                              <span className="text-sm font-medium">{alert.whaleName}</span>
                            </div>
                            <span className="text-xs text-slate-500">{new Date(alert.timestamp).toLocaleString()}</span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3">
                            <div>
                              <p className="text-xs text-slate-500">Token</p>
                              <p className="text-sm font-medium">{alert.tokenSymbol}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Buy Amount</p>
                              <p className="text-sm font-bold text-amber-400">{formatUsd(alert.buyAmountUsd)}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Market Cap</p>
                              <p className="text-sm">{formatUsd(alert.marketCap)}</p>
                            </div>
                            <div>
                              <p className="text-xs text-slate-500">Liquidity</p>
                              <p className="text-sm">{formatUsd(alert.liquidity)}</p>
                            </div>
                          </div>
                          {alert.tokenAddress && (
                            <div className="mt-2 pt-2 border-t border-slate-700/50">
                              <code className="text-xs text-slate-400 break-all">{alert.tokenAddress}</code>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Wallets Tab */}
          <TabsContent value="wallets" className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold">Whale Wallets ({wallets.length})</h2>
              <Button onClick={seedWallets} variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800">
                <Zap className="w-4 h-4 mr-2" />
                Seed Default Wallets
              </Button>
            </div>

            {/* Add Wallet Form */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Plus className="w-4 h-4 text-amber-500" />
                  Add New Wallet
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="name" className="text-xs text-slate-400">Wallet Name</Label>
                    <Input id="name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="e.g. Ansem" className="bg-slate-800 border-slate-700" />
                  </div>
                  <div>
                    <Label htmlFor="address" className="text-xs text-slate-400">Wallet Address</Label>
                    <Input id="address" value={newAddress} onChange={(e) => setNewAddress(e.target.value)} placeholder="0x... or Solana address" className="bg-slate-800 border-slate-700 font-mono text-sm" />
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-400">Network</Label>
                    <Select value={newNetwork} onValueChange={setNewNetwork}>
                      <SelectTrigger className="w-32 bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="solana">🟢 Solana</SelectItem>
                        <SelectItem value="ethereum">🟣 Ethereum</SelectItem>
                        <SelectItem value="bsc">🟡 BSC</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-400">Famous Dev</Label>
                    <Switch checked={newFamous} onCheckedChange={setNewFamous} />
                  </div>
                  <Button onClick={addWallet} className="ml-auto bg-amber-500 hover:bg-amber-600 text-black">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Wallet
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Wallet List */}
            <Card className="bg-slate-900 border-slate-800">
              <CardContent className="p-0">
                <ScrollArea className="h-[500px]">
                  <div className="divide-y divide-slate-800">
                    {wallets.length === 0 ? (
                      <div className="text-center py-12">
                        <Wallet className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <p className="text-slate-400">No wallets yet</p>
                        <p className="text-xs text-slate-500 mt-1">Click "Seed Default Wallets" to add famous whales</p>
                      </div>
                    ) : (
                      wallets.map((wallet) => (
                        <div key={wallet.id} className="flex items-center justify-between p-4 hover:bg-slate-800/50 transition-colors">
                          <div className="flex items-center gap-3">
                            <span className="text-lg">{networkIcon(wallet.network)}</span>
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-medium">{wallet.name}</p>
                                {wallet.isFamous && <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/30 text-xs">FAMOUS</Badge>}
                              </div>
                              <p className="text-xs text-slate-400 font-mono">{wallet.address.slice(0, 20)}...{wallet.address.slice(-6)}</p>
                              {wallet.note && <p className="text-xs text-slate-500">{wallet.note}</p>}
                            </div>
                          </div>
                          <Button
                            onClick={() => removeWallet(wallet.address)}
                            variant="ghost"
                            size="icon"
                            className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))
                    )}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Files Tab */}
          <TabsContent value="files" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <File className="w-5 h-5 text-amber-500" />
                  VPS File Manager
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                  <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Globe className="w-4 h-4 text-green-400" />
                    VPS Connection
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-slate-500">Host:</span>{' '}
                      <code className="text-green-400">13.48.105.23</code>
                    </div>
                    <div>
                      <span className="text-slate-500">User:</span>{' '}
                      <code className="text-green-400">ubuntu</code>
                    </div>
                    <div>
                      <span className="text-slate-500">Project:</span>{' '}
                      <code className="text-green-400">/home/ubuntu/telegram-whale-bot</code>
                    </div>
                    <div>
                      <span className="text-slate-500">Key:</span>{' '}
                      <code className="text-green-400">bot-server-key.pem</code>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-medium">Quick Actions</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <Button variant="outline" className="border-slate-700 hover:bg-slate-800 justify-start" onClick={() => navigator.clipboard.writeText('ssh -i "C:\\Users\\pc\\Desktop\\aws\\bot-server-key.pem" ubuntu@13.48.105.23')}>
                      <span className="mr-2">🔌</span> Copy SSH Command
                    </Button>
                    <Button variant="outline" className="border-slate-700 hover:bg-slate-800 justify-start" onClick={() => navigator.clipboard.writeText('docker compose down && docker compose up -d --build')}>
                      <span className="mr-2">🔄</span> Copy Restart Command
                    </Button>
                    <Button variant="outline" className="border-slate-700 hover:bg-slate-800 justify-start" onClick={() => navigator.clipboard.writeText('docker logs -f whale-bot-solana')}>
                      <span className="mr-2">📋</span> Copy Solana Logs
                    </Button>
                    <Button variant="outline" className="border-slate-700 hover:bg-slate-800 justify-start" onClick={() => navigator.clipboard.writeText('docker logs -f whale-bot-eth')}>
                      <span className="mr-2">📋</span> Copy ETH Logs
                    </Button>
                  </div>
                </div>

                <div className="space-y-3">
                  <h3 className="text-sm font-medium">Docker Containers</h3>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">🟢</span>
                        <span className="text-sm">whale-bot-solana</span>
                      </div>
                      <Badge variant="outline" className="border-green-500/30 text-green-400">Running</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">🟡</span>
                        <span className="text-sm">whale-bot-bsc</span>
                      </div>
                      <Badge variant="outline" className="border-green-500/30 text-green-400">Running</Badge>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">🟣</span>
                        <span className="text-sm">whale-bot-eth</span>
                      </div>
                      <Badge variant="outline" className="border-green-500/30 text-green-400">Running</Badge>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-amber-500/5 border border-amber-500/20">
                  <p className="text-xs text-amber-400/80">
                    💡 To manage files directly, use the SSH command to connect to your VPS.
                    The dashboard runs alongside the bot and provides a quick overview.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5 text-amber-500" />
                  Bot Settings
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-slate-300">Min Buy USD</Label>
                    <p className="text-xs text-slate-500 mb-2">Minimum buy amount to trigger alert</p>
                    <div className="flex items-center gap-2">
                      <Input value={minBuy} onChange={(e) => setMinBuy(e.target.value)} className="bg-slate-800 border-slate-700" />
                      <Button size="sm" variant="outline" className="border-slate-700">Save</Button>
                    </div>
                  </div>
                  <div>
                    <Label className="text-sm text-slate-300">Max Buy USD</Label>
                    <p className="text-xs text-slate-500 mb-2">Maximum buy amount (skip large buys)</p>
                    <div className="flex items-center gap-2">
                      <Input value={maxBuy} onChange={(e) => setMaxBuy(e.target.value)} className="bg-slate-800 border-slate-700" />
                      <Button size="sm" variant="outline" className="border-slate-700">Save</Button>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50">
                  <div>
                    <Label className="text-sm text-slate-300">Only Famous Devs</Label>
                    <p className="text-xs text-slate-500">Only send alerts for famous developers</p>
                  </div>
                  <Switch checked={onlyFamous} onCheckedChange={setOnlyFamous} />
                </div>

                <div className="p-4 rounded-lg bg-slate-800/50">
                  <h3 className="text-sm font-medium mb-3">API Keys</h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Helius API:</span>
                      <code className="text-green-400">✅ Active</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Etherscan API:</span>
                      <code className="text-green-400">✅ Active</code>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Telegram Bot:</span>
                      <code className="text-green-400">✅ Active</code>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-slate-800/50">
                  <h3 className="text-sm font-medium mb-3">VPS Info</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-slate-500">IP:</span> <code className="text-slate-300">13.48.105.23</code></div>
                    <div><span className="text-slate-500">OS:</span> <code className="text-slate-300">Ubuntu</code></div>
                    <div><span className="text-slate-500">Containers:</span> <code className="text-slate-300">3</code></div>
                    <div><span className="text-slate-500">Network:</span> <code className="text-slate-300">3 chains</code></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-800 bg-slate-950/80">
        <div className="container mx-auto px-4 py-4 text-center text-xs text-slate-500">
          Whale Tracker Dashboard · Built with Next.js · Connected to VPS 13.48.105.23
        </div>
      </footer>
    </div>
  )
}
