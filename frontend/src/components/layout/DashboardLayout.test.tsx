import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import DashboardLayout from './DashboardLayout'
import { BrowserRouter } from 'react-router'

describe('DashboardLayout', () => {
  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <DashboardLayout>
          <div>Test Content</div>
        </DashboardLayout>
      </BrowserRouter>
    )
    expect(screen.getByText('Test Content')).toBeInTheDocument()
  })
})
