import apiClient from './client'

export const uploadApi = {
  uploadPhoto: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post('/upload/photo', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  deletePhoto: async (photoId: string) => {
    const { data } = await apiClient.delete(`/upload/photo/${photoId}`)
    return data
  },

  setPrimaryPhoto: async (photoId: string) => {
    const { data } = await apiClient.patch(`/upload/photo/${photoId}/set-primary`)
    return data
  },

  submitIdentityVerification: async (idDocument: File, selfie: File) => {
    const form = new FormData()
    form.append('id_document', idDocument)
    form.append('selfie', selfie)
    const { data } = await apiClient.post('/verification/submit-identity-documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  submitBlueTick: async (matchSelfie: File) => {
    const form = new FormData()
    form.append('match_selfie', matchSelfie)
    const { data } = await apiClient.post('/verification/submit-blue-tick-documents', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  getVerificationStatus: async () => {
    const { data } = await apiClient.get('/verification/status')
    return data
  },
}
