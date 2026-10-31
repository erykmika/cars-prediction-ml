export interface FeatureField {
  name: string
  label: string
  type: 'text' | 'number' | 'select'
  required: boolean
  options?: string[]
  min?: number
  max?: number
  step?: number
  placeholder?: string
}

export const FEATURE_SCHEMA: FeatureField[] = [
  {
    name: 'brand',
    label: 'Brand',
    type: 'select',
    required: true,
    options: [
      'Toyota',
      'Volkswagen',
      'BMW',
      'Audi',
      'Mercedes-Benz',
      'Ford',
      'Opel',
      'Renault',
      'Peugeot',
      'Citroën',
      'Fiat',
      'Skoda',
      'Hyundai',
      'Kia',
      'Nissan',
      'Mazda',
      'Honda',
      'Suzuki',
      'Mitsubishi',
      'Subaru',
      'Volvo',
      'Other',
    ],
  },
  {
    name: 'model',
    label: 'Model',
    type: 'text',
    required: true,
    placeholder: 'e.g. Corolla',
  },
  {
    name: 'year',
    label: 'Year',
    type: 'number',
    required: true,
    min: 1990,
    max: new Date().getFullYear(),
    step: 1,
  },
  {
    name: 'mileage',
    label: 'Mileage (km)',
    type: 'number',
    required: true,
    min: 0,
    step: 1000,
  },
  {
    name: 'fuel_type',
    label: 'Fuel Type',
    type: 'select',
    required: true,
    options: ['Petrol', 'Diesel', 'Hybrid', 'Electric', 'LPG'],
  },
  {
    name: 'gearbox',
    label: 'Transmission',
    type: 'select',
    required: true,
    options: ['Manual', 'Automatic'],
  },
  {
    name: 'engine_capacity',
    label: 'Engine Capacity (L)',
    type: 'number',
    required: true,
    min: 0.5,
    max: 8.0,
    step: 0.1,
  },
]