import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { PredictionForm } from '../components/PredictionForm'
import type { PredictionRequest, PredictionResponse } from '../types/api'

export const Predict = () => {
  const { logout } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<PredictionResponse | null>(null)

  const handlePredict = async (data: PredictionRequest) => {
    setIsLoading(true)
    setResult(null)
    try {
      const response = await import('../api/client').then(m => m.default.post<PredictionResponse>('/predict', data))
      setResult(response.data)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900">Car Price Prediction</h1>
          <p className="mt-2 text-gray-600">
            Fill in the vehicle details to get a price estimate
          </p>
        </div>

        <div className="bg-white shadow rounded-lg p-8">
          <PredictionForm onPredict={handlePredict} isLoading={isLoading} result={result} />
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={() => logout()}
            className="text-sm text-blue-600 hover:text-blue-500"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}