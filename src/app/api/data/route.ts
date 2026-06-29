import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'

export async function GET() {
  try {
    const wallets = await db.whaleWallet.findMany({
      orderBy: { createdAt: 'desc' }
    })

    const alerts = await db.buyAlert.findMany({
      take: 50,
      orderBy: { createdAt: 'desc' }
    })

    const totalWallets = wallets.length
    const famousWallets = wallets.filter(w => w.isFamous).length
    const solanaWallets = wallets.filter(w => w.network === 'solana').length
    const ethWallets = wallets.filter(w => w.network === 'ethereum').length
    const totalAlerts = await db.buyAlert.count()
    const gemAlerts = alerts.filter(a => a.isGem).length

    return NextResponse.json({
      wallets,
      alerts,
      stats: {
        totalWallets,
        famousWallets,
        solanaWallets,
        ethWallets,
        totalAlerts,
        gemAlerts,
      }
    })
  } catch (error) {
    console.error('Stats error:', error)
    return NextResponse.json({ error: 'Failed to fetch stats' }, { status: 500 })
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { action } = body

    if (action === 'addWallet') {
      const wallet = await db.whaleWallet.create({
        data: {
          name: body.name,
          address: body.address,
          network: body.network || 'solana',
          isFamous: body.isFamous || false,
          source: body.source || 'manual',
          note: body.note || null,
        }
      })
      return NextResponse.json(wallet)
    }

    if (action === 'removeWallet') {
      await db.whaleWallet.delete({
        where: { address: body.address }
      })
      return NextResponse.json({ success: true })
    }

    if (action === 'addAlert') {
      const alert = await db.buyAlert.create({
        data: {
          whaleName: body.whaleName,
          whaleAddress: body.whaleAddress,
          network: body.network || 'solana',
          tokenSymbol: body.tokenSymbol,
          tokenName: body.tokenName,
          tokenAddress: body.tokenAddress,
          buyAmount: body.buyAmount || 0,
          buyAmountUsd: body.buyAmountUsd || 0,
          tokenPrice: body.tokenPrice || 0,
          marketCap: body.marketCap || 0,
          liquidity: body.liquidity || 0,
          volume24h: body.volume24h || 0,
          txHash: body.txHash || null,
          isGem: body.isGem || false,
        }
      })
      return NextResponse.json(alert)
    }

    if (action === 'seedWallets') {
      const defaultWallets = [
        { name: 'Ansem', address: 'AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm', network: 'solana', isFamous: true, source: 'FAMOUS_DEV', note: 'Maker of ANSEM $80M' },
        { name: 'Murad', address: '7QZGS7MQ4S6hRmE8iXoFTXgQ2hXVUCho2ZhgeWvLNPZT', network: 'solana', isFamous: true, source: 'FAMOUS_DEV', note: '$24M portfolio' },
        { name: 'Murad ETH', address: '0x8b194370825e37b33373e74a41009161808c1488', network: 'ethereum', isFamous: true, source: 'FAMOUS_DEV', note: '$24M ETH' },
        { name: 'Mundi Trader', address: '5ow9M5AZUDUm3p3PAeBYMA8g2n65fKRMrfdbqEyE2b6U', network: 'solana', isFamous: true, source: 'FAMOUS_DEV', note: '1 SOL to $435K (2580x)' },
        { name: 'shatter.sol', address: 'H2ikJvq8or5MyjvFowD7CDY6fG3Sc2yi4mxTnfovXy3K', network: 'solana', isFamous: false, source: 'Nansen', note: '$35M on TRUMP' },
        { name: 'PEPE Whale', address: '0xa43fe16908251ee70ef74718545e4fe6c5ccec9f', network: 'ethereum', isFamous: false, source: 'PEPE_HOLDER', note: '$17M portfolio' },
      ]

      for (const w of defaultWallets) {
        await db.whaleWallet.upsert({
          where: { address: w.address },
          update: w,
          create: w,
        })
      }

      return NextResponse.json({ success: true, count: defaultWallets.length })
    }

    return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
  } catch (error) {
    console.error('API error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}
