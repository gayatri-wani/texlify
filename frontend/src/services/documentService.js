import api from '../utils/api'

export const documentService = {
  upload: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  getAll: async () => {
    const response = await api.get('/documents')
    return response.data
  },

  delete: async (id) => {
    const response = await api.delete(`/documents/${id}`)
    return response.data
  },

  sendCommand: async (documentId, command) => {
    const response = await api.post(`/documents/${documentId}/command`, { command })
    return response.data
  },

  selectionCommand: async (documentId, params) => {
    const response = await api.post(
      `/documents/${documentId}/selection-command`, params)
    return response.data
  },

  getPreview: async (documentId) => {
    const response = await api.get(`/documents/${documentId}/preview`, {
      responseType: 'text',
      headers: { 'Accept': 'text/html' }
    })
    return response.data
  },

  download: async (id, filename) => {
    const response = await api.get(`/documents/${id}/download`, {
      responseType: 'blob',
    })
    const url  = window.URL.createObjectURL(new Blob([response.data]))
    const link = window.document.createElement('a')
    link.href  = url
    link.setAttribute('download', filename)
    window.document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  },
}