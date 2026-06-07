import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, it, expect } from 'vitest'
import LeadsPage from './LeadsPage'

describe('LeadsPage', () => {
  const renderPage = () => {
    return render(
      <MemoryRouter>
        <LeadsPage />
      </MemoryRouter>
    )
  }

  it('renders the leads page title', () => {
    renderPage()
    expect(screen.getByText('Leads')).toBeDefined()
    expect(screen.getByText('Manage and qualify your B2B leads from multiple sources.')).toBeDefined()
  })

  it('filters leads by company name', () => {
    renderPage()
    const searchInput = screen.getByPlaceholderText('Search leads...')
    
    fireEvent.change(searchInput, { target: { value: 'TechFlow' } })
    
    expect(screen.getByText('TechFlow Systems')).toBeDefined()
    expect(screen.queryByText('FinStream AI')).toBeNull()
  })

  it('filters leads by industry', () => {
    renderPage()
    const searchInput = screen.getByPlaceholderText('Search leads...')
    
    fireEvent.change(searchInput, { target: { value: 'Fintech' } })
    
    expect(screen.getByText('FinStream AI')).toBeDefined()
    expect(screen.queryByText('TechFlow Systems')).toBeNull()
  })

  it('displays the correct score for a lead', () => {
    renderPage()
    // TechFlow Systems has score 88
    const scoreElement = screen.getByText('88')
    expect(scoreElement).toBeDefined()
  })

  it('renders the correct status labels', () => {
    renderPage()
    expect(screen.getAllByText('qualified hot').length).toBeGreaterThan(0)
    expect(screen.getAllByText('qualified warm').length).toBeGreaterThan(0)
  })
})
