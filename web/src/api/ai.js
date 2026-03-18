export const chatWithAI = async (message, onChunk, onQuery) => {
  const token = localStorage.getItem('token')
  const response = await fetch('http://localhost:8000/api/ai/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    throw new Error(`请求失败: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const text = decoder.decode(value, { stream: true })
    buffer += text

    while (buffer.length > 0) {
      if (buffer.startsWith('[QUERYING]')) {
        const end = buffer.indexOf('\n')
        if (end === -1) break
        const line = buffer.slice(0, end)
        onQuery && onQuery(line.replace('[QUERYING]', '').trim())
        buffer = buffer.slice(end + 1)
      } else {
        const queryIdx = buffer.indexOf('[QUERYING]')
        if (queryIdx === -1) {
          onChunk && onChunk(buffer)
          buffer = ''
        } else {
          onChunk && onChunk(buffer.slice(0, queryIdx))
          buffer = buffer.slice(queryIdx)
        }
      }
    }
  }

  if (buffer && !buffer.startsWith('[QUERYING]')) {
    onChunk && onChunk(buffer)
  }
}