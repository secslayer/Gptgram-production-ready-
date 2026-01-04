import { useState } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Textarea } from '../components/ui/textarea'
import { Label } from '../components/ui/label'
import { Badge } from '../components/ui/badge'
import {
  Save,
  AlertCircle,
  Check,
  Code,
  FileText,
  Bot
} from 'lucide-react'

export default function AgentCreationFixed() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    type: 'custom',
    category: 'general',
    webhook_url: '',
    price_cents: 10,
    tags: [],
    input_schema: {
      type: 'object',
      required: ['input'],
      properties: {
        input: { type: 'string', description: 'Input data' }
      }
    },
    output_schema: {
      type: 'object',
      properties: {
        output: { type: 'string', description: 'Output data' }
      }
    },
    example_input: {
      input: 'Example input text'
    },
    example_output: {
      output: 'Example output text'
    }
  })
  
  const [isSaving, setIsSaving] = useState(false)
  const [saveStatus, setSaveStatus] = useState(null)
  const [errors, setErrors] = useState({})
  const [currentTag, setCurrentTag] = useState('')

  const validateForm = () => {
    const newErrors = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Agent name is required'
    }
    
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    }
    
    try {
      JSON.stringify(formData.input_schema)
    } catch {
      newErrors.input_schema = 'Invalid JSON schema'
    }
    
    try {
      JSON.stringify(formData.output_schema)
    } catch {
      newErrors.output_schema = 'Invalid JSON schema'
    }
    
    try {
      JSON.stringify(formData.example_input)
    } catch {
      newErrors.example_input = 'Invalid JSON'
    }
    
    try {
      JSON.stringify(formData.example_output)
    } catch {
      newErrors.example_output = 'Invalid JSON'
    }
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSave = async () => {
    if (!validateForm()) {
      setSaveStatus({ type: 'error', message: 'Please fix validation errors' })
      return
    }
    
    setIsSaving(true)
    setSaveStatus(null)
    
    try {
      const response = await axios.post('http://localhost:8000/api/agents/create', {
        name: formData.name,
        description: formData.description,
        type: formData.type,
        category: formData.category,
        webhook_url: formData.webhook_url,
        price_cents: parseInt(formData.price_cents),
        tags: formData.tags,
        input_schema: formData.input_schema,
        output_schema: formData.output_schema,
        example_input: formData.example_input,
        example_output: formData.example_output
      })
      
      if (response.data.success) {
        setSaveStatus({ 
          type: 'success', 
          message: `Agent "${formData.name}" created successfully!`,
          agent_id: response.data.agent_id
        })
        
        // Reset form after success
        setTimeout(() => {
          setFormData({
            name: '',
            description: '',
            type: 'custom',
            category: 'general',
            webhook_url: '',
            price_cents: 10,
            tags: [],
            input_schema: {
              type: 'object',
              required: ['input'],
              properties: {
                input: { type: 'string', description: 'Input data' }
              }
            },
            output_schema: {
              type: 'object',
              properties: {
                output: { type: 'string', description: 'Output data' }
              }
            },
            example_input: { input: 'Example input text' },
            example_output: { output: 'Example output text' }
          })
          setSaveStatus(null)
        }, 3000)
      }
    } catch (error) {
      setSaveStatus({ 
        type: 'error', 
        message: `Failed to create agent: ${error.response?.data?.detail || error.message}`
      })
    } finally {
      setIsSaving(false)
    }
  }

  const handleSchemaChange = (field, value) => {
    try {
      const parsed = JSON.parse(value)
      setFormData({ ...formData, [field]: parsed })
      setErrors({ ...errors, [field]: null })
    } catch {
      setErrors({ ...errors, [field]: 'Invalid JSON' })
    }
  }

  const handleExampleChange = (field, value) => {
    try {
      const parsed = JSON.parse(value)
      setFormData({ ...formData, [field]: parsed })
      setErrors({ ...errors, [field]: null })
    } catch {
      setErrors({ ...errors, [field]: 'Invalid JSON' })
    }
  }

  const addTag = () => {
    if (currentTag.trim() && !formData.tags.includes(currentTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, currentTag.trim()]
      })
      setCurrentTag('')
    }
  }

  const removeTag = (tag) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(t => t !== tag)
    })
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Create New Agent</h1>
        <p className="text-muted-foreground">
          Define your agent's capabilities, schemas, and examples
        </p>
      </div>

      {saveStatus && (
        <div className={`mb-4 p-4 rounded-lg flex items-start space-x-2 ${
          saveStatus.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {saveStatus.type === 'success' ? (
            <Check className="h-5 w-5 mt-0.5" />
          ) : (
            <AlertCircle className="h-5 w-5 mt-0.5" />
          )}
          <div>
            <div className="font-medium">{saveStatus.message}</div>
            {saveStatus.agent_id && (
              <div className="text-sm mt-1">Agent ID: {saveStatus.agent_id}</div>
            )}
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bot className="h-5 w-5 mr-2" />
              Basic Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="name">Agent Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Text Summarizer"
                  className={errors.name ? 'border-red-500' : ''}
                />
                {errors.name && (
                  <p className="text-red-500 text-xs mt-1">{errors.name}</p>
                )}
              </div>
              
              <div>
                <Label htmlFor="type">Type</Label>
                <select
                  id="type"
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="custom">Custom</option>
                  <option value="n8n">n8n Webhook</option>
                  <option value="api">API</option>
                </select>
              </div>
            </div>
            
            <div>
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Describe what your agent does..."
                rows={3}
                className={errors.description ? 'border-red-500' : ''}
              />
              {errors.description && (
                <p className="text-red-500 text-xs mt-1">{errors.description}</p>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category">Category</Label>
                <select
                  id="category"
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="general">General</option>
                  <option value="text">Text Processing</option>
                  <option value="analysis">Analysis</option>
                  <option value="translation">Translation</option>
                  <option value="generation">Generation</option>
                </select>
              </div>
              
              <div>
                <Label htmlFor="price">Price (cents)</Label>
                <Input
                  id="price"
                  type="number"
                  min="0"
                  value={formData.price_cents}
                  onChange={(e) => setFormData({ ...formData, price_cents: e.target.value })}
                />
              </div>
            </div>
            
            {formData.type === 'n8n' && (
              <div>
                <Label htmlFor="webhook">Webhook URL</Label>
                <Input
                  id="webhook"
                  type="url"
                  value={formData.webhook_url}
                  onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                  placeholder="https://n8n.example.com/webhook/..."
                />
              </div>
            )}
            
            <div>
              <Label>Tags</Label>
              <div className="flex space-x-2 mb-2">
                <Input
                  value={currentTag}
                  onChange={(e) => setCurrentTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addTag())}
                  placeholder="Add tag..."
                />
                <Button type="button" onClick={addTag} variant="outline">
                  Add
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                {formData.tags.map((tag, idx) => (
                  <Badge key={idx} variant="secondary">
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="ml-2 text-xs hover:text-red-500"
                    >
                      ×
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Schema Definition */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Code className="h-5 w-5 mr-2" />
              Schema Definition
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="input-schema">Input Schema (JSON Schema) *</Label>
              <Textarea
                id="input-schema"
                value={JSON.stringify(formData.input_schema, null, 2)}
                onChange={(e) => handleSchemaChange('input_schema', e.target.value)}
                className={`font-mono text-sm ${errors.input_schema ? 'border-red-500' : ''}`}
                rows={8}
                placeholder="Define the expected input structure..."
              />
              {errors.input_schema && (
                <p className="text-red-500 text-xs mt-1">{errors.input_schema}</p>
              )}
            </div>
            
            <div>
              <Label htmlFor="output-schema">Output Schema (JSON Schema) *</Label>
              <Textarea
                id="output-schema"
                value={JSON.stringify(formData.output_schema, null, 2)}
                onChange={(e) => handleSchemaChange('output_schema', e.target.value)}
                className={`font-mono text-sm ${errors.output_schema ? 'border-red-500' : ''}`}
                rows={8}
                placeholder="Define the output structure..."
              />
              {errors.output_schema && (
                <p className="text-red-500 text-xs mt-1">{errors.output_schema}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Examples */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Examples
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="example-input">Example Input (JSON) *</Label>
              <Textarea
                id="example-input"
                value={JSON.stringify(formData.example_input, null, 2)}
                onChange={(e) => handleExampleChange('example_input', e.target.value)}
                className={`font-mono text-sm ${errors.example_input ? 'border-red-500' : ''}`}
                rows={6}
                placeholder="Provide an example input..."
              />
              {errors.example_input && (
                <p className="text-red-500 text-xs mt-1">{errors.example_input}</p>
              )}
            </div>
            
            <div>
              <Label htmlFor="example-output">Example Output (JSON) *</Label>
              <Textarea
                id="example-output"
                value={JSON.stringify(formData.example_output, null, 2)}
                onChange={(e) => handleExampleChange('example_output', e.target.value)}
                className={`font-mono text-sm ${errors.example_output ? 'border-red-500' : ''}`}
                rows={6}
                placeholder="Provide the expected output for the example input..."
              />
              {errors.example_output && (
                <p className="text-red-500 text-xs mt-1">{errors.example_output}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end space-x-2">
          <Button
            variant="outline"
            onClick={() => window.location.href = '/agents'}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Save Agent
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
