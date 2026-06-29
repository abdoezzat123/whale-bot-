import { NextRequest, NextResponse } from 'next/server'
import { Client } from 'ssh2'
import { readFileSync } from 'fs'
import { join } from 'path'

const VPS_HOST = '13.48.105.23'
const VPS_USER = 'ubuntu'
const VPS_KEY_PATH = join(process.cwd(), 'bot-server-key.pem')
const VPS_PROJECT_DIR = '/home/ubuntu/telegram-whale-bot'

function getSSHClient(): Promise<Client> {
  return new Promise((resolve, reject) => {
    const conn = new Client()
    let keyContent: string | Buffer
    
    try {
      keyContent = readFileSync(VPS_KEY_PATH, 'utf-8')
    } catch {
      // لو الملف مش موجود، نستخدم الـ key من البيئة
      keyContent = process.env.VPS_SSH_KEY || ''
    }

    conn.on('ready', () => resolve(conn))
    conn.on('error', (err) => reject(err))
    
    conn.connect({
      host: VPS_HOST,
      port: 22,
      username: VPS_USER,
      privateKey: keyContent,
      readyTimeout: 15000,
    })
  })
}

function execCommand(conn: Client, command: string): Promise<{ stdout: string; stderr: string }> {
  return new Promise((resolve, reject) => {
    conn.exec(command, (err, stream) => {
      if (err) return reject(err)
      let stdout = ''
      let stderr = ''
      stream.on('close', () => resolve({ stdout, stderr }))
      stream.on('data', (data: Buffer) => { stdout += data.toString() })
      stream.stderr.on('data', (data: Buffer) => { stderr += data.toString() })
    })
  })
}

export async function GET() {
  return NextResponse.json({
    status: 'info',
    message: 'VPS API is running. Use POST with action.',
    vpsHost: VPS_HOST,
    projectDir: VPS_PROJECT_DIR,
  })
}

export async function POST(req: NextRequest) {
  const body = await req.json()
  const { action } = body

  try {
    const conn = await getSSHClient()

    try {
      // ===== STATUS: عرض حالة الحاويات =====
      if (action === 'status') {
        const { stdout } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && docker ps --format "{{.Names}}|{{.Status}}|{{.Image}}"')
        const containers = stdout.trim().split('\n').filter(Boolean).map(line => {
          const [name, status, image] = line.split('|')
          return { name, status, image }
        })
        
        // نحسب عدد المحافظ
        const { stdout: walletsOut } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && grep -c "address" whales.py 2>/dev/null || echo 0')
        const walletCount = parseInt(walletsOut.trim()) || 0
        
        // نقرأ .env
        const { stdout: envOut } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && cat .env 2>/dev/null')
        const envLines = envOut.trim().split('\n')
        const minBuy = envLines.find(l => l.startsWith('MIN_BUY_USD'))?.split('=')[1] || '50'
        const maxBuy = envLines.find(l => l.startsWith('MAX_BUY_USD'))?.split('=')[1] || '2000000'
        const onlyFamous = envLines.find(l => l.startsWith('ONLY_FAMOUS'))?.split('=')[1] || 'false'
        const heliusKey = envLines.find(l => l.startsWith('HELIUS_API_KEY'))?.split('=')[1] || ''
        const etherscanKey = envLines.find(l => l.startsWith('ETHERSCAN_API_KEY'))?.split('=')[1] || ''

        return NextResponse.json({
          success: true,
          containers,
          walletCount,
          settings: {
            minBuy,
            maxBuy,
            onlyFamous,
            heliusKey: heliusKey ? '✅ Active' : '❌ Missing',
            etherscanKey: etherscanKey ? '✅ Active' : '❌ Missing',
          }
        })
      }

      // ===== RESTART: إعادة تشغيل البوت =====
      if (action === 'restart') {
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && docker compose down && docker compose up -d --build 2>&1')
        return NextResponse.json({
          success: true,
          message: 'Bot restarted successfully',
          output: stdout + stderr,
        })
      }

      // ===== STOP: إيقاف البوت =====
      if (action === 'stop') {
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && docker compose down 2>&1')
        return NextResponse.json({
          success: true,
          message: 'Bot stopped',
          output: stdout + stderr,
        })
      }

      // ===== START: تشغيل البوت =====
      if (action === 'start') {
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && docker compose up -d --build 2>&1')
        return NextResponse.json({
          success: true,
          message: 'Bot started',
          output: stdout + stderr,
        })
      }

      // ===== LOGS: عرض الـ logs =====
      if (action === 'logs') {
        const container = body.container || 'whale-bot-solana'
        const lines = body.lines || 30
        const { stdout } = await execCommand(conn, 'docker logs --tail ' + lines + ' ' + container + ' 2>&1')
        return NextResponse.json({
          success: true,
          logs: stdout,
          container,
        })
      }

      // ===== LIST FILES: عرض الملفات =====
      if (action === 'listFiles') {
        const { stdout } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && ls -la --time-style=long-iso 2>&1')
        const files = stdout.trim().split('\n').slice(1).map(line => {
          const parts = line.trim().split(/\s+/)
          if (parts.length < 8) return null
          const perms = parts[0]
          const size = parts[4]
          const date = parts[5]
          const time = parts[6]
          const name = parts.slice(7).join(' ')
          return { name, size, date, time, isDir: perms.startsWith('d'), perms }
        }).filter(Boolean)
        return NextResponse.json({ success: true, files })
      }

      // ===== DELETE FILE: حذف ملف =====
      if (action === 'deleteFile') {
        const filename = body.filename
        if (!filename || filename.includes('..') || filename.includes('/')) {
          return NextResponse.json({ error: 'Invalid filename' }, { status: 400 })
        }
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && rm -f ' + filename + ' 2>&1')
        return NextResponse.json({ success: true, message: 'File deleted: ' + filename, output: stdout + stderr })
      }

      // ===== READ FILE: قراءة محتوى ملف =====
      if (action === 'readFile') {
        const filename = body.filename
        if (!filename || filename.includes('..') || filename.includes('/')) {
          return NextResponse.json({ error: 'Invalid filename' }, { status: 400 })
        }
        const { stdout } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && cat ' + filename + ' 2>&1')
        return NextResponse.json({ success: true, content: stdout, filename })
      }

      // ===== WRITE FILE: كتابة محتوى ملف =====
      if (action === 'writeFile') {
        const filename = body.filename
        const content = body.content
        if (!filename || filename.includes('..') || filename.includes('/')) {
          return NextResponse.json({ error: 'Invalid filename' }, { status: 400 })
        }
        // نكتب الملف باستخدام cat مع heredoc
        const escapedContent = content.replace(/'/g, "'\\''")
        const { stdout, stderr } = await execCommand(conn, "cd " + VPS_PROJECT_DIR + " && cat > " + filename + " << 'ENDOFFILE'\n" + content + "\nENDOFFILE\n2>&1")
        return NextResponse.json({ success: true, message: 'File saved: ' + filename, output: stdout + stderr })
      }

      // ===== UPDATE .env: تحديث الإعدادات =====
      if (action === 'updateEnv') {
        const { minBuy, maxBuy, onlyFamous } = body
        let cmd = 'cd ' + VPS_PROJECT_DIR + ' && '
        if (minBuy !== undefined) cmd += "sed -i 's/MIN_BUY_USD=.*/MIN_BUY_USD=" + minBuy + "/' .env && "
        if (maxBuy !== undefined) cmd += "sed -i 's/MAX_BUY_USD=.*/MAX_BUY_USD=" + maxBuy + "/' .env && "
        if (onlyFamous !== undefined) cmd += "sed -i 's/ONLY_FAMOUS=.*/ONLY_FAMOUS=" + onlyFamous + "/' .env && "
        cmd += 'echo "Done"'
        const { stdout, stderr } = await execCommand(conn, cmd)
        return NextResponse.json({ success: true, message: 'Settings updated', output: stdout + stderr })
      }

      // ===== GIT PULL: تحديث من GitHub =====
      if (action === 'gitPull') {
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && git pull 2>&1')
        return NextResponse.json({ success: true, message: 'Git pull done', output: stdout + stderr })
      }

      // ===== BUILD: إعادة بناء الحاويات =====
      if (action === 'build') {
        const { stdout, stderr } = await execCommand(conn, 'cd ' + VPS_PROJECT_DIR + ' && docker compose up -d --build 2>&1')
        return NextResponse.json({ success: true, message: 'Build done', output: stdout + stderr })
      }

      return NextResponse.json({ error: 'Unknown action: ' + action }, { status: 400 })
    } finally {
      conn.end()
    }
  } catch (error: any) {
    console.error('VPS API error:', error)
    return NextResponse.json({
      success: false,
      error: error.message || 'SSH connection failed',
      hint: 'Make sure bot-server-key.pem is in the project root',
    }, { status: 500 })
  }
}
