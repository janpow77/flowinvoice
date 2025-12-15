import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => api.getProject(id!),
    enabled: !!id,
  })

  if (isLoading) {
    return <div className="animate-pulse">Lade Projekt...</div>
  }

  if (!project) {
    return <div>Projekt nicht gefunden</div>
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900">{project.title}</h2>
        <p className="mt-2 text-gray-500">{project.description}</p>
      </div>
    </div>
  )
}
