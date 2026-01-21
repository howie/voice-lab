/**
 * Jobs Page
 * T045: Main page for job management
 *
 * Feature: 007-async-job-mgmt
 */

import { useState } from 'react'
import { Briefcase } from 'lucide-react'
import { JobList, JobDetail } from '@/components/jobs'

export function JobsPage() {
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Briefcase className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-2xl font-bold">背景工作</h1>
          <p className="text-muted-foreground">
            管理和追蹤您的多角色 TTS 合成工作
          </p>
        </div>
      </div>

      {/* Content */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Job List */}
        <div className="rounded-xl border bg-card p-6">
          <JobList
            onSelectJob={setSelectedJobId}
            selectedJobId={selectedJobId}
          />
        </div>

        {/* Job Detail */}
        <div className="rounded-xl border bg-card p-6">
          <JobDetail
            jobId={selectedJobId}
            onClose={() => setSelectedJobId(null)}
          />
        </div>
      </div>
    </div>
  )
}
