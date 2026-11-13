import { Link } from 'react-router-dom'
import { Layout } from '../components/layout/Layout'
import { Button } from '@carbon/react'

export function TemplateListPage() {
  return (
    <Layout>
      <div className="p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-normal">Checklist Templates</h1>
          <Button as={Link} to="/templates/TPL-SYN-001">
            Open Template
          </Button>
        </div>
        <p className="text-sm text-gray-600">Template list coming soon.</p>
      </div>
    </Layout>
  )
}
