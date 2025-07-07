import { NextRequest } from 'next/server';

// Store connected clients
const clients = new Set<ReadableStreamDefaultController>();

export async function GET(request: NextRequest) {
  const stream = new ReadableStream({
    start(controller: ReadableStreamDefaultController) {
      clients.add(controller);
      
      // Send initial connection message
      controller.enqueue(`data: ${JSON.stringify({
        level: 'INFO',
        message: 'Log stream connected'
      })}\n\n`);
    },
    cancel(controller: ReadableStreamDefaultController) {
      clients.delete(controller);
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET',
      'Access-Control-Allow-Headers': 'Cache-Control',
    },
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { level = 'INFO', message } = body;
    
    const logData = JSON.stringify({ level, message, timestamp: new Date().toISOString() });
    
    // Send to all connected clients
    clients.forEach(client => {
      try {
        client.enqueue(`data: ${logData}\n\n`);
      } catch (error) {
        // Remove disconnected clients
        clients.delete(client);
      }
    });
    
    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: 'Invalid request' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }
} 