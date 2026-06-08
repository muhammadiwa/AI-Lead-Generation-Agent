import { useEffect, useState, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  payload: any
}

export function useWebSocket(url: string) {
  const [messages, setMessages] = useState<WebSocketMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)

  useEffect(() => {
    // In a real app, you'd use the actual URL
    // For now, we simulate the connection if it's a "mock" URL
    if (url === 'mock') {
      setIsConnected(true)
      const interval = setInterval(() => {
        const mockMessage = {
          type: 'LEAD_UPDATE',
          payload: {
            id: Math.floor(Math.random() * 10).toString(),
            status: 'qualified_hot',
            score: Math.floor(Math.random() * 100),
          }
        }
        setMessages((prev) => [...prev.slice(-19), mockMessage])
      }, 10000)
      return () => clearInterval(interval)
    }

    const socket = new WebSocket(url)

    socket.onopen = () => {
      setIsConnected(true)
    }

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setMessages((prev) => [...prev.slice(-19), data])
    }

    socket.onclose = () => {
      setIsConnected(false)
    }

    setWs(socket)

    return () => {
      socket.close()
    }
  }, [url])

  const sendMessage = useCallback((type: string, payload: any) => {
    if (ws && isConnected) {
      ws.send(JSON.stringify({ type, payload }))
    }
  }, [ws, isConnected])

  return { messages, isConnected, sendMessage }
}
