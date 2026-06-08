import { useState } from 'react'
import { 
  ChevronRight, 
  ChevronLeft, 
  Check, 
  Mail, 
  Linkedin, 
  MessageSquare,
  Clock,
  Plus,
  Trash2,
  Layout
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { clsx } from 'clsx'

const steps = [
  { id: 'details', title: 'Campaign Details' },
  { id: 'targeting', title: 'Targeting (ICP)' },
  { id: 'sequence', title: 'Sequence Builder' },
  { id: 'templates', title: 'Message Templates' },
  { id: 'review', title: 'Review & Launch' },
]

export default function CreateCampaignPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    goal: 'lead_generation',
    industries: [] as string[],
    companySize: '10-50',
    channels: ['email'] as string[],
    sequence: [
      { id: '1', day: 0, channel: 'email', templateId: 'initial-outreach' }
    ],
  })

  const nextStep = () => setCurrentStep((prev) => Math.min(prev + 1, steps.length - 1))
  const prevStep = () => setCurrentStep((prev) => Math.max(prev - 1, 0))

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Create New Campaign</h1>
        <p className="mt-1 text-sm text-gray-500">
          Follow the steps below to set up your automated outreach campaign.
        </p>
      </div>

      {/* Stepper */}
      <nav aria-label="Progress">
        <ol role="list" className="flex items-center">
          {steps.map((step, stepIdx) => (
            <li key={step.id} className={clsx(stepIdx !== steps.length - 1 ? 'pr-8 sm:pr-20' : '', 'relative')}>
              {stepIdx < currentStep ? (
                <>
                  <div className="absolute inset-0 flex items-center" aria-hidden="true">
                    <div className="h-0.5 w-full bg-indigo-600" />
                  </div>
                  <button
                    onClick={() => setCurrentStep(stepIdx)}
                    className="relative flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 hover:bg-indigo-900"
                  >
                    <Check className="h-5 w-5 text-white" aria-hidden="true" />
                    <span className="sr-only">{step.title}</span>
                  </button>
                </>
              ) : stepIdx === currentStep ? (
                <>
                  <div className="absolute inset-0 flex items-center" aria-hidden="true">
                    <div className="h-0.5 w-full bg-gray-200" />
                  </div>
                  <button
                    className="relative flex h-8 w-8 items-center justify-center rounded-full border-2 border-indigo-600 bg-white"
                    aria-current="step"
                  >
                    <span className="h-2.5 w-2.5 rounded-full bg-indigo-600" aria-hidden="true" />
                    <span className="sr-only">{step.title}</span>
                  </button>
                </>
              ) : (
                <>
                  <div className="absolute inset-0 flex items-center" aria-hidden="true">
                    <div className="h-0.5 w-full bg-gray-200" />
                  </div>
                  <button className="group relative flex h-8 w-8 items-center justify-center rounded-full border-2 border-gray-300 bg-white hover:border-gray-400">
                    <span className="h-2.5 w-2.5 rounded-full bg-transparent group-hover:bg-gray-300" aria-hidden="true" />
                    <span className="sr-only">{step.title}</span>
                  </button>
                </>
              )}
              <div className="absolute top-10 -left-1/2 w-32 text-center text-[10px] font-medium uppercase tracking-wider text-gray-500">
                {step.title}
              </div>
            </li>
          ))}
        </ol>
      </nav>

      {/* Step Content */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mt-12">
        {currentStep === 0 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">Step 1: Campaign Details</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Campaign Name</label>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  placeholder="e.g. Q3 Startup Outreach"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  placeholder="What is this campaign about?"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Goal</label>
                <select
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  value={formData.goal}
                  onChange={(e) => setFormData({ ...formData, goal: e.target.value })}
                >
                  <option value="lead_generation">Lead Generation</option>
                  <option value="market_research">Market Research</option>
                  <option value="event_promotion">Event Promotion</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {currentStep === 1 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">Step 2: Ideal Customer Profile (ICP)</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Industries</label>
                <p className="text-xs text-gray-500 mb-2">Select industries to target (comma separated for now)</p>
                <input
                  type="text"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
                  placeholder="SaaS, Fintech, Healthtech"
                  onChange={(e) => setFormData({ ...formData, industries: e.target.value.split(',').map(s => s.trim()) })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Company Size</label>
                <div className="mt-2 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {['1-10', '10-50', '50-200', '200-500', '500+'].map((size) => (
                    <button
                      key={size}
                      type="button"
                      onClick={() => setFormData({ ...formData, companySize: size })}
                      className={clsx(
                        'flex items-center justify-center rounded-md border py-2 px-3 text-sm font-semibold uppercase sm:flex-1',
                        formData.companySize === size
                          ? 'bg-indigo-600 text-white border-transparent'
                          : 'bg-white text-gray-900 border-gray-200 hover:bg-gray-50'
                      )}
                    >
                      {size}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStep === 2 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Step 3: Outreach Sequence</h2>
              <button 
                onClick={() => setFormData({
                  ...formData,
                  sequence: [...formData.sequence, { id: Date.now().toString(), day: 3, channel: 'email', templateId: '' }]
                })}
                className="inline-flex items-center gap-1 text-sm font-medium text-indigo-600 hover:text-indigo-500"
              >
                <Plus className="h-4 w-4" /> Add Step
              </button>
            </div>
            
            <div className="space-y-4">
              {formData.sequence.map((step, index) => (
                <div key={step.id} className="flex items-center gap-4 p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <div className="flex flex-col items-center justify-center w-12 h-12 rounded-full bg-white border border-gray-200 text-indigo-600 font-bold">
                    {index + 1}
                  </div>
                  <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase">Wait Time</label>
                      <div className="mt-1 flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-400" />
                        <input 
                          type="number" 
                          className="block w-full rounded-md border-gray-300 sm:text-sm border p-1"
                          value={step.day}
                          onChange={(e) => {
                            const newSeq = [...formData.sequence]
                            newSeq[index].day = parseInt(e.target.value)
                            setFormData({ ...formData, sequence: newSeq })
                          }}
                        />
                        <span className="text-sm text-gray-500 whitespace-nowrap">days after</span>
                      </div>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase">Channel</label>
                      <select 
                        className="mt-1 block w-full rounded-md border-gray-300 sm:text-sm border p-1"
                        value={step.channel}
                        onChange={(e) => {
                          const newSeq = [...formData.sequence]
                          newSeq[index].channel = e.target.value
                          setFormData({ ...formData, sequence: newSeq })
                        }}
                      >
                        <option value="email">Email</option>
                        <option value="linkedin">LinkedIn</option>
                        <option value="whatsapp">WhatsApp</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-gray-500 uppercase">Template</label>
                      <select className="mt-1 block w-full rounded-md border-gray-300 sm:text-sm border p-1">
                        <option>Initial Outreach</option>
                        <option>Follow up #1</option>
                        <option>Value Add</option>
                        <option>Break-up Email</option>
                      </select>
                    </div>
                  </div>
                  <button 
                    onClick={() => {
                      const newSeq = formData.sequence.filter((_, i) => i !== index)
                      setFormData({ ...formData, sequence: newSeq })
                    }}
                    className="p-2 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="h-5 w-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {currentStep === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">Step 4: Message Templates</h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 space-y-2">
                {formData.sequence.map((step, index) => (
                  <button
                    key={step.id}
                    className="w-full flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 text-left"
                  >
                    <div className="flex-shrink-0 w-8 h-8 rounded bg-indigo-100 flex items-center justify-center text-indigo-600">
                      {step.channel === 'email' ? <Mail className="h-4 w-4" /> : <Linkedin className="h-4 w-4" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Step {index + 1}: {step.channel}</p>
                      <p className="text-xs text-gray-500">Day {step.day}</p>
                    </div>
                  </button>
                ))}
              </div>
              <div className="lg:col-span-2 space-y-4 border border-gray-200 rounded-lg p-6 bg-gray-50">
                <div className="flex items-center justify-between">
                  <h3 className="text-md font-medium text-gray-900 flex items-center gap-2">
                    <Layout className="h-4 w-4" /> Editor: Initial Outreach (Email)
                  </h3>
                  <div className="flex gap-2">
                    <button className="px-2 py-1 text-xs bg-white border border-gray-300 rounded shadow-sm hover:bg-gray-50">Preview</button>
                    <button className="px-2 py-1 text-xs bg-indigo-600 text-white rounded shadow-sm hover:bg-indigo-700">Save</button>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase">Subject</label>
                    <input 
                      type="text" 
                      className="mt-1 block w-full rounded-md border-gray-300 sm:text-sm border p-2 bg-white"
                      defaultValue="Quick thought on {{company_name}}'s tech setup"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase">Body</label>
                    <textarea 
                      rows={10}
                      className="mt-1 block w-full rounded-md border-gray-300 sm:text-sm border p-2 bg-white font-mono text-sm"
                      defaultValue={`Hi {{first_name}},\n\nI noticed {{company_name}} is using {{tech_stack}} for your frontend. We've helped similar companies scale their engineering teams by 30%.\n\nWould you be open to a quick chat next Tuesday?`}
                    />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {['{{first_name}}', '{{company_name}}', '{{tech_stack}}', '{{role}}'].map(tag => (
                      <span key={tag} className="px-2 py-1 bg-indigo-50 text-indigo-700 rounded text-xs border border-indigo-100 cursor-pointer hover:bg-indigo-100">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {currentStep === 4 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-gray-900">Step 5: Review & Launch</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Campaign Overview</h3>
                  <dl className="mt-2 space-y-2">
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Name</dt>
                      <dd className="font-medium text-gray-900">{formData.name || 'Unnamed Campaign'}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Goal</dt>
                      <dd className="font-medium text-gray-900 capitalize">{formData.goal.replace('_', ' ')}</dd>
                    </div>
                    <div className="flex justify-between text-sm">
                      <dt className="text-gray-500">Target Size</dt>
                      <dd className="font-medium text-gray-900">{formData.companySize} employees</dd>
                    </div>
                  </dl>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Targeting</h3>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {formData.industries.map(industry => (
                      <span key={industry} className="px-2 py-1 bg-white border border-gray-200 rounded text-xs text-gray-700">
                        {industry}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Sequence Summary</h3>
                <div className="relative pl-8 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-200">
                  {formData.sequence.map((step, i) => (
                    <div key={step.id} className="relative">
                      <div className="absolute -left-8 flex h-6 w-6 items-center justify-center rounded-full bg-white border-2 border-indigo-600">
                        <div className="h-1.5 w-1.5 rounded-full bg-indigo-600" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-gray-900">
                          {i === 0 ? 'Day 0: Initial Outreach' : `Day ${step.day}: Follow up`}
                        </p>
                        <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                          {step.channel === 'email' ? <Mail className="h-3 w-3" /> : <Linkedin className="h-3 w-3" />}
                          via {step.channel}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="mt-10 pt-6 border-t border-gray-200 flex items-center justify-between">
          <button
            onClick={prevStep}
            disabled={currentStep === 0}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
          >
            <ChevronLeft className="h-4 w-4" /> Back
          </button>
          
          {currentStep === steps.length - 1 ? (
            <button
              onClick={() => navigate('/campaigns')}
              className="flex items-center gap-2 rounded-md bg-green-600 px-6 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
            >
              Launch Campaign
            </button>
          ) : (
            <button
              onClick={nextStep}
              className="flex items-center gap-2 rounded-md bg-indigo-600 px-6 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Next Step <ChevronRight className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
