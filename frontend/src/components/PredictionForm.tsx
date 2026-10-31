import { useState } from 'react'
import { FEATURE_SCHEMA, type FeatureField } from '../config/features'
import type { PredictionRequest, PredictionResponse } from '../types/api'

interface PredictionFormProps {
  onPredict: (data: PredictionRequest) => Promise<void>
  isLoading: boolean
  result: PredictionResponse | null
}

export const PredictionForm = ({ onPredict, isLoading, result }: PredictionFormProps) => {
  const [formData, setFormData] = useState<Record<string, any>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [predictError, setPredictError] = useState('')

  const handleChange = (field: FeatureField, value: any) => {
    setFormData((prev) => ({ ...prev, [field.name]: value }))
    if (errors[field.name]) {
      setErrors((prev) => ({ ...prev, [field.name]: '' }))
    }
  }

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}
    FEATURE_SCHEMA.forEach((field) => {
      const value = formData[field.name]
      if (field.required && (value === '' || value === undefined || value === null)) {
        newErrors[field.name] = `${field.label} is required`
      } else if (field.type === 'number' && value !== '' && value !== undefined) {
        const num = Number(value)
        if (isNaN(num)) {
          newErrors[field.name] = `${field.label} must be a number`
        } else {
          if (field.min !== undefined && num < field.min) {
            newErrors[field.name] = `${field.label} must be at least ${field.min}`
          }
          if (field.max !== undefined && num > field.max) {
            newErrors[field.name] = `${field.label} must be at most ${field.max}`
          }
        }
      }
    })
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setPredictError('')
    if (!validate()) return

    const features = FEATURE_SCHEMA.reduce((acc, field) => {
      const value = formData[field.name]
      if (field.type === 'number') {
        let num = value !== '' && value !== undefined ? Number(value) : null
        // Convert engine capacity from liters to cubic centimeters
        if (field.name === 'engine_capacity' && num !== null) {
          num = Math.round(num * 1000)
        }
        acc[field.name] = num
      } else {
        acc[field.name] = value || null
      }
      return acc
    }, {} as Record<string, any>)

    try {
      await onPredict({ features })
    } catch (err: any) {
      setPredictError(err.response?.data?.detail || 'Prediction failed. Please try again.')
    }
  }

  return (
    <div className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid gap-6 sm:grid-cols-2">
          {FEATURE_SCHEMA.map((field) => (
            <div key={field.name} className="space-y-1">
              <label htmlFor={field.name} className="block text-sm font-medium text-gray-700">
                {field.label} {field.required && <span className="text-red-500">*</span>}
              </label>
              {field.type === 'select' ? (
                <select
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] || ''}
                  onChange={(e) => handleChange(field, e.target.value)}
                  className={`mt-1 block w-full rounded-md border ${errors[field.name] ? 'border-red-500' : 'border-gray-300'} shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2`}
                >
                  <option value="">Select...</option>
                  {field.options?.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type={field.type}
                  id={field.name}
                  name={field.name}
                  value={formData[field.name] ?? ''}
                  onChange={(e) => handleChange(field, e.target.value)}
                  placeholder={field.placeholder}
                  min={field.min}
                  max={field.max}
                  step={field.step}
                  className={`mt-1 block w-full rounded-md border ${errors[field.name] ? 'border-red-500' : 'border-gray-300'} shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm p-2`}
                  required={field.required}
                />
              )}
              {errors[field.name] && (
                <p className="mt-1 text-sm text-red-600">{errors[field.name]}</p>
              )}
            </div>
          ))}
        </div>

        {predictError && (
          <div className="bg-red-50 text-red-600 p-3 rounded-md text-sm" role="alert">
            {predictError}
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Predicting...' : 'Predict Price'}
          </button>
        </div>
      </form>

      {result && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <h3 className="text-lg font-medium text-green-800">Predicted Price</h3>
          <p className="mt-1 text-2xl font-bold text-green-900">
            {typeof result.prediction === 'number' ? `${result.prediction.toLocaleString()} PLN` : result.prediction}
          </p>
        </div>
      )}
    </div>
  )
}