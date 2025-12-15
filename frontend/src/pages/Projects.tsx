import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FolderOpen, Plus, Calendar, FileText } from 'lucide-react'
import { api } from '@/lib/api'

export default function Projects() {
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.getProjects(),
  })

  if (isLoading) {
    return <div className="animate-pulse">Lade Projekte...</div>
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900">Projekte</h2>
        <button className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
          <Plus className="h-5 w-5 mr-2" />
          Neues Projekt
        </button>
      </div>

      {/* Project Grid */}
      {projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: any) => (
            <Link
              key={project.id}
              to={`/projects/${project.id}`}
              className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start">
                <div className="p-2 bg-primary-50 rounded-lg">
                  <FolderOpen className="h-6 w-6 text-primary-600" />
                </div>
                <div className="ml-4 flex-1">
                  <h3 className="font-medium text-gray-900">{project.title}</h3>
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                    {project.description || 'Keine Beschreibung'}
                  </p>
                </div>
              </div>

              <div className="mt-4 flex items-center text-sm text-gray-500 space-x-4">
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {project.start_date} - {project.end_date}
                </span>
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  {project.document_count || 0} Dokumente
                </span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <FolderOpen className="h-12 w-12 text-gray-400 mx-auto" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">Keine Projekte</h3>
          <p className="mt-2 text-sm text-gray-500">
            Erstellen Sie ein neues Projekt, um Rechnungen zu organisieren.
          </p>
          <button className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
            Projekt erstellen
          </button>
        </div>
      )}
    </div>
  )
}
