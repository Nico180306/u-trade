interface Env {
  BACKEND_ORIGIN?: string
  INTERNAL_PROXY_SECRET?: string
}

interface PagesFunctionContext {
  request: Request
  env: Env
}

const FORWARDED_REQUEST_HEADERS = [
  'cookie',
  'origin',
  'referer',
  'content-type',
  'x-csrftoken',
  'accept',
] as const

export async function onRequest(context: PagesFunctionContext): Promise<Response> {
  const { request, env } = context

  if (!env.BACKEND_ORIGIN || !env.INTERNAL_PROXY_SECRET) {
    return new Response(
      JSON.stringify({
        code: 'PROXY_MISCONFIGURED',
        message: 'El proxy de API no está configurado correctamente.',
        details: {},
      }),
      {
        status: 502,
        headers: {
          'Content-Type': 'application/json; charset=utf-8',
          'Cache-Control': 'no-store',
        },
      },
    )
  }

  const incomingUrl = new URL(request.url)
  const upstreamUrl = new URL(
    `${incomingUrl.pathname}${incomingUrl.search}`,
    env.BACKEND_ORIGIN,
  )

  const upstreamHeaders = new Headers()
  for (const headerName of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(headerName)
    if (value !== null) {
      upstreamHeaders.set(headerName, value)
    }
  }

  upstreamHeaders.set('X-Internal-Proxy-Secret', env.INTERNAL_PROXY_SECRET)
  upstreamHeaders.set('X-Client-IP', request.headers.get('CF-Connecting-IP') || '')

  const hasBody = request.method !== 'GET' && request.method !== 'HEAD'
  const upstreamResponse = await fetch(upstreamUrl.toString(), {
    method: request.method,
    headers: upstreamHeaders,
    body: hasBody ? request.body : undefined,
    redirect: 'manual',
  })

  // Clonar Headers directamente preserva múltiples cabeceras Set-Cookie (prohibido Object.fromEntries).
  const responseHeaders = new Headers(upstreamResponse.headers)

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  })
}
