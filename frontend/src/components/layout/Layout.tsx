import { ReactNode } from 'react'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { Theme, Content } from '@carbon/react'

interface LayoutProps {
  children: ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <Theme theme="white">
      <Header />
      <div className="app-layout">
        <Sidebar />
        <Content className="app-main">{children}</Content>
      </div>
    </Theme>
  )
}
