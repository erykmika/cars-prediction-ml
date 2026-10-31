import { Routes, Route, Navigate } from 'react-router-dom'
import { Login } from './pages/Login'
import { Predict } from './pages/Predict'
import { ProtectedRoute } from './pages/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/predict" element={<Predict />} />
      </Route>
      <Route path="/" element={<Navigate to="/predict" replace />} />
      <Route path="*" element={<Navigate to="/predict" replace />} />
    </Routes>
  )
}

export default App