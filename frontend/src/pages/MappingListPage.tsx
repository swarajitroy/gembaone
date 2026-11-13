import { useNavigate } from 'react-router-dom'

export default function MappingListPage() {
  const navigate = useNavigate()
  
  // Navigate to mapping editor for demonstration
  // In a real app, this would show a list of mappings
  setTimeout(() => {
    navigate('/mappings/1')
  }, 0)
  
  return null
}
