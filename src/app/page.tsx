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
import { Textarea } from '@/components/ui/textarea'
import { Wallet, Zap, Settings, File, Plus, X, Globe, Activity, Gem, RefreshCw, Play, Square, Terminal, Upload, Save, Trash2, GitBranch, AlertCircle, CheckCircle2 } from 'lucide-react'

interface Container {
  name: string
  status: string
  image: string
}

interface VpsFile {
  name: string
  size: string
  date: string
  time: string
  isDir: boolean
  perms: string
}

export default function Home() {
  const [activeTab, setActiveTab] = useState('dashboard')
  
  // VPS State
  const [containers, setContainers] = useState<Container[]>([])
  const [walletCount, setWalletCount] = useState(0)
  const [vpsSettings, setVpsSettings] = useState({ minBuy: '50', maxBuy: '2000000', onlyFamous: 'false', heliusKey: '', etherscanKey: '' })
  const [vpsConnected, setVpsConnected] = useState(false)
  const [vpsLoading, setVpsLoading] = useState(false)
  const [vpsMessage, setVpsMessage] = useState('')
  const [vpsError, setVpsError] = useState('')

  // Logs
  const [logContainer, setLogContainer] = useState('whale-bot-solana')
  const [logContent, setLogContent] = useState('')
  const [logLines, setLogLines] = useState(30)

  // Files
  const [files, setFiles] = useState<VpsFile[]>([])
  const [selectedFile, setSelectedFile] = useState('')
  const [fileContent, setFileContent] = useState('')
  const [fileEditing, setFileEditing] = useState(false)

  // Settings form
  const [setMinBuy, setSetMinBuy] = useState('50')
  const [setMaxBuy, setSetMaxBuy] = useState('2000000')
  const [setOnlyFamous, setSetOnlyFamous] = useState(false)

  // Add wallet form
  const [newName, setNewName] = useState('')
  const [newAddress, setNewAddress] = useState('')
  const [newNetwork, setNewNetwork] = useState('solana')
  const [newFamous, setNewFamous] = useState(false)

  const vpsApi = async (action: string, extra: Record<string, unknown> = {}) => {
    setVpsLoading(true)
    setVpsMessage('')
    setVpsError('')
    try {
      const res = await fetch('/api/vps', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...extra }),
      })
      const data = await res.json()
      if (data.success) {
        setVpsConnected(true)
        if (data.message) setVpsMessage(data.message)
        return data
      } else {
        setVpsError(data.error || 'Unknown error')
        setVpsConnected(false)
        return null
      }
    } catch (e: unknown) {
      setVpsError(e instanceof Error ? e.message : 'Connection failed')
      setVpsConnected(false)
      return null
    } finally {
      setVpsLoading(false)
    }
  }

  const fetchStatus = useCallback(async () => {
    const data = await vpsApi('status')
    if (data?.success) {
      setContainers(data.containers || [])
      setWalletCount(data.walletCount || 0)
      setVpsSettings(data.settings || {})
      setSetMinBuy(data.settings?.minBuy || '50')
      setSetMaxBuy(data.settings?.maxBuy || '2000000')
      setSetOnlyFamous(data.settings?.onlyFamous === 'true')
    }
  }, [])

  const fetchLogs = async () => {
    const data = await vpsApi('logs', { container: logContainer, lines: logLines })
    if (data?.success) {
      setLogContent(data.logs || 'No logs')
    }
  }

  const fetchFiles = async () => {
    const data = await vpsApi('listFiles')
    if (data?.success) {
      setFiles(data.files || [])
    }
  }

  const readFile = async (filename: string) => {
    const data = await vpsApi('readFile', { filename })
    if (data?.success) {
      setSelectedFile(filename)
      setFileContent(data.content || '')
      setFileEditing(true)
    }
  }

  const saveFile = async () => {
    if (!selectedFile) return
    const data = await vpsApi('writeFile', { filename: selectedFile, content: fileContent })
    if (data?.success) {
      setVpsMessage('File saved: ' + selectedFile)
      setFileEditing(false)
    }
  }

  const deleteFile = async (filename: string) => {
    if (!confirm('Delete ' + filename + '?')) return
    const data = await vpsApi('deleteFile', { filename })
    if (data?.success) {
      setVpsMessage('Deleted: ' + filename)
      fetchFiles()
    }
  }

  const updateSettings = async () => {
    const data = await vpsApi('updateEnv', {
      minBuy: setMinBuy,
      maxBuy: setMaxBuy,
      onlyFamous: setOnlyFamous ? 'true' : 'false',
    })
    if (data?.success) {
      setVpsMessage('Settings updated! Restart bot to apply.')
      fetchStatus()
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [fetchStatus])

  const formatUsd = (val: number) => {
    if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`
    if (val >= 1e6) return `$${(val / 1e6).toFixed(1)}M`
    if (val >= 1e3) return `$${(val / 1e3).toFixed(1)}K`
    if (val > 0) return `$${val.toFixed(4)}`
    return '?'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Wallet className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Whale Tracker</h1>
              <p className="text-xs text-slate-400">VPS Connected Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {vpsConnected ? (
              <Badge variant="outline" className="border-green-500/50 text-green-400">
                <CheckCircle2 className="w-3 h-3 mr-1" /> VPS Online
              </Badge>
            ) : (
              <Badge variant="outline" className="border-red-500/50 text-red-400">
                <AlertCircle className="w-3 h-3 mr-1" /> VPS Offline
              </Badge>
            )}
            <Badge variant="outline" className="border-amber-500/50 text-amber-400">
              <Activity className="w-3 h-3 mr-1" /> {walletCount} Wallets
            </Badge>
          </div>
        </div>
      </header>

      {vpsMessage && (
        <div className="bg-green-500/10 border-b border-green-500/20 px-4 py-2 text-sm text-green-400 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {vpsMessage}
          <button onClick={() => setVpsMessage('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}
      {vpsError && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" /> {vpsError}
          <button onClick={() => setVpsError('')} className="ml-auto"><X className="w-4 h-4" /></button>
        </div>
      )}

      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 md:grid-cols-5 mb-6 bg-slate-900 border border-slate-800">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Activity className="w-4 h-4 mr-2" /><span className="hidden sm:inline">Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="control" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Terminal className="w-4 h-4 mr-2" /><span className="hidden sm:inline">Control</span>
            </TabsTrigger>
            <TabsTrigger value="files" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <File className="w-4 h-4 mr-2" /><span className="hidden sm:inline">Files</span>
            </TabsTrigger>
            <TabsTrigger value="logs" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Terminal className="w-4 h-4 mr-2" /><span className="hidden sm:inline">Logs</span>
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-amber-500/20 data-[state=active]:text-amber-400">
              <Settings className="w-4 h-4 mr-2" /><span className="hidden sm:inline">Settings</span>
            </TabsTrigger>
          </TabsList>

          {/* ===== DASHBOARD ===== */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Wallet className="w-5 h-5 text-amber-500" />
                    <Badge variant="secondary" className="bg-amber-500/10 text-amber-400 text-xs">Total</Badge>
                  </div>
                  <p className="text-3xl font-bold">{walletCount}</p>
                  <p className="text-xs text-slate-400">Tracked Wallets</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Activity className="w-5 h-5 text-green-500" />
                    <Badge variant="secondary" className="bg-green-500/10 text-green-400 text-xs">Active</Badge>
                  </div>
                  <p className="text-3xl font-bold">{containers.length}</p>
                  <p className="text-xs text-slate-400">Docker Containers</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Globe className="w-5 h-5 text-blue-500" />
                    <Badge variant="secondary" className="bg-blue-500/10 text-blue-400 text-xs">VPS</Badge>
                  </div>
                  <p className="text-3xl font-bold text-sm">13.48.105.23</p>
                  <p className="text-xs text-slate-400">AWS EC2 Instance</p>
                </CardContent>
              </Card>
              <Card className="bg-slate-900 border-slate-800">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Zap className="w-5 h-5 text-yellow-500" />
                    <Badge variant="secondary" className="bg-yellow-500/10 text-yellow-400 text-xs">Min Buy</Badge>
                  </div>
                  <p className="text-3xl font-bold">${vpsSettings.minBuy}</p>
                  <p className="text-xs text-slate-400">Min Buy USD</p>
                </CardContent>
              </Card>
            </div>

            {/* Containers */}
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Activity className="w-5 h-5 text-amber-500" />
                  Docker Containers
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {containers.length === 0 ? (
                    <p className="text-slate-400 text-sm text-center py-4">No containers running. Start the bot from Control tab.</p>
                  ) : (
                    containers.map((c) => (
                      <div key={c.name} className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{c.name.includes('solana') ? '🟢' : c.name.includes('eth') ? '🟣' : '🟡'}</span>
                          <div>
                            <p className="text-sm font-medium">{c.name}</p>
                            <p className="text-xs text-slate-400">{c.image}</p>
                          </div>
                        </div>
                        <Badge variant="outline" className={c.status.includes('Up') ? 'border-green-500/30 text-green-400' : 'border-red-500/30 text-red-400'}>
                          {c.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-3">
              <Button onClick={() => fetchStatus()} variant="outline" className="border-slate-700 hover:bg-slate-800" disabled={vpsLoading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${vpsLoading ? 'animate-spin' : ''}`} />
                Refresh Status
              </Button>
            </div>
          </TabsContent>

          {/* ===== CONTROL ===== */}
          <TabsContent value="control" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Terminal className="w-5 h-5 text-amber-500" />
                  Bot Control Panel
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Button onClick={() => vpsApi('start')} className="bg-green-600 hover:bg-green-700" disabled={vpsLoading}>
                    <Play className="w-4 h-4 mr-2" /> Start
                  </Button>
                  <Button onClick={() => vpsApi('stop')} className="bg-red-600 hover:bg-red-700" disabled={vpsLoading}>
                    <Square className="w-4 h-4 mr-2" /> Stop
                  </Button>
                  <Button onClick={() => vpsApi('restart')} className="bg-amber-600 hover:bg-amber-700" disabled={vpsLoading}>
                    <RefreshCw className={`w-4 h-4 mr-2 ${vpsLoading ? 'animate-spin' : ''}`} /> Restart
                  </Button>
                  <Button onClick={() => vpsApi('build')} variant="outline" className="border-slate-700 hover:bg-slate-800" disabled={vpsLoading}>
                    <RefreshCw className="w-4 h-4 mr-2" /> Build
                  </Button>
                </div>

                <div className="border-t border-slate-800 pt-4 space-y-3">
                  <h3 className="text-sm font-medium flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-amber-500" />
                    Git Operations
                  </h3>
                  <Button onClick={() => vpsApi('gitPull')} variant="outline" className="border-slate-700 hover:bg-slate-800" disabled={vpsLoading}>
                    <GitBranch className="w-4 h-4 mr-2" /> Git Pull (Update from GitHub)
                  </Button>
                  <p className="text-xs text-slate-500">Pulls latest code from GitHub, then restart the bot to apply.</p>
                </div>

                <div className="border-t border-slate-800 pt-4">
                  <h3 className="text-sm font-medium mb-2">VPS Info</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div><span className="text-slate-500">IP:</span> <code className="text-green-400">13.48.105.23</code></div>
                    <div><span className="text-slate-500">User:</span> <code className="text-green-400">ubuntu</code></div>
                    <div><span className="text-slate-500">Project:</span> <code className="text-green-400">telegram-whale-bot</code></div>
                    <div><span className="text-slate-500">OS:</span> <code className="text-green-400">Ubuntu</code></div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ===== FILES ===== */}
          <TabsContent value="files" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <File className="w-5 h-5 text-amber-500" />
                    VPS File Manager
                  </CardTitle>
                  <Button onClick={fetchFiles} variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800">
                    <RefreshCw className="w-4 h-4 mr-2" /> Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {files.length === 0 ? (
                  <p className="text-slate-400 text-sm text-center py-4">Click Refresh to load files</p>
                ) : (
                  <ScrollArea className="h-64">
                    <div className="space-y-1">
                      {files.map((f) => (
                        <div key={f.name} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-800/50 transition-colors">
                          <div className="flex items-center gap-2">
                            <span>{f.isDir ? '📁' : '📄'}</span>
                            <button onClick={() => readFile(f.name)} className="text-sm hover:text-amber-400 transition-colors">
                              {f.name}
                            </button>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-xs text-slate-500">{f.size}</span>
                            {!f.isDir && f.name !== '.env' && (
                              <button onClick={() => deleteFile(f.name)} className="text-red-400 hover:text-red-300">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>

            {/* File Editor */}
            {fileEditing && (
              <Card className="bg-slate-900 border-slate-800">
                <CardHeader>
                  <CardTitle className="text-sm flex items-center gap-2">
                    <File className="w-4 h-4 text-amber-500" />
                    Editing: {selectedFile}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <Textarea
                    value={fileContent}
                    onChange={(e) => setFileContent(e.target.value)}
                    className="bg-slate-800 border-slate-700 font-mono text-sm min-h-[300px]"
                    placeholder="File content..."
                  />
                  <div className="flex gap-2">
                    <Button onClick={saveFile} className="bg-green-600 hover:bg-green-700">
                      <Save className="w-4 h-4 mr-2" /> Save
                    </Button>
                    <Button onClick={() => { setFileEditing(false); setSelectedFile('') }} variant="outline" className="border-slate-700">
                      Cancel
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* ===== LOGS ===== */}
          <TabsContent value="logs" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <div className="flex items-center justify-between flex-wrap gap-3">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-amber-500" />
                    Container Logs
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Select value={logContainer} onValueChange={setLogContainer}>
                      <SelectTrigger className="w-48 bg-slate-800 border-slate-700">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-slate-700">
                        <SelectItem value="whale-bot-solana">🟢 Solana</SelectItem>
                        <SelectItem value="whale-bot-bsc">🟡 BSC</SelectItem>
                        <SelectItem value="whale-bot-eth">🟣 Ethereum</SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      type="number"
                      value={logLines}
                      onChange={(e) => setLogLines(parseInt(e.target.value) || 30)}
                      className="w-20 bg-slate-800 border-slate-700"
                      min={5}
                      max={200}
                    />
                    <Button onClick={fetchLogs} variant="outline" size="sm" className="border-slate-700 hover:bg-slate-800">
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <pre className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono text-slate-300 max-h-[500px] overflow-auto whitespace-pre-wrap">
                  {logContent || 'Click refresh to load logs...'}
                </pre>
              </CardContent>
            </Card>
          </TabsContent>

          {/* ===== SETTINGS ===== */}
          <TabsContent value="settings" className="space-y-4">
            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Settings className="w-5 h-5 text-amber-500" />
                  Bot Settings (Live on VPS)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm text-slate-300">Min Buy USD</Label>
                    <p className="text-xs text-slate-500 mb-2">Minimum buy to trigger alert</p>
                    <Input value={setMinBuy} onChange={(e) => setSetMinBuy(e.target.value)} className="bg-slate-800 border-slate-700" />
                  </div>
                  <div>
                    <Label className="text-sm text-slate-300">Max Buy USD</Label>
                    <p className="text-xs text-slate-500 mb-2">Skip large buys above this</p>
                    <Input value={setMaxBuy} onChange={(e) => setSetMaxBuy(e.target.value)} className="bg-slate-800 border-slate-700" />
                  </div>
                </div>
                <div className="flex items-center justify-between p-4 rounded-lg bg-slate-800/50">
                  <div>
                    <Label className="text-sm text-slate-300">Only Famous Devs</Label>
                    <p className="text-xs text-slate-500">Only alert for famous developers</p>
                  </div>
                  <Switch checked={setOnlyFamous} onCheckedChange={setSetOnlyFamous} />
                </div>
                <Button onClick={updateSettings} className="bg-amber-500 hover:bg-amber-600 text-black" disabled={vpsLoading}>
                  <Save className="w-4 h-4 mr-2" /> Save & Apply on VPS
                </Button>

                <div className="border-t border-slate-800 pt-4">
                  <h3 className="text-sm font-medium mb-3">API Keys</h3>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between p-2 rounded bg-slate-800/50">
                      <span className="text-slate-500">Helius API:</span>
                      <span className={vpsSettings.heliusKey?.includes('✅') ? 'text-green-400' : 'text-red-400'}>{vpsSettings.heliusKey}</span>
                    </div>
                    <div className="flex justify-between p-2 rounded bg-slate-800/50">
                      <span className="text-slate-500">Etherscan API:</span>
                      <span className={vpsSettings.etherscanKey?.includes('✅') ? 'text-green-400' : 'text-red-400'}>{vpsSettings.etherscanKey}</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <footer className="mt-auto border-t border-slate-800 bg-slate-950/80">
        <div className="container mx-auto px-4 py-4 text-center text-xs text-slate-500">
          Whale Tracker · Connected to VPS 13.48.105.23 · {containers.length} containers running
        </div>
      </footer>
    </div>
  )
}
