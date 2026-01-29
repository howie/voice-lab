/**
 * Music Generation Page
 * Feature: 012-music-generation
 *
 * Main page for music generation using Mureka AI.
 */

import { useEffect, useState } from 'react'
import { MusicForm, MusicJobList, MusicPlayer, QuotaDisplay } from '@/components/music'
import { useMusicStore } from '@/stores/musicStore'
import type { MusicJob } from '@/types/music'

export function MusicPage() {
  const { currentJob, setCurrentJob, fetchJobs, retryJob } = useMusicStore()
  const [selectedJob, setSelectedJob] = useState<MusicJob | null>(null)

  // Initial load
  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  // Sync selected job with currentJob
  useEffect(() => {
    if (currentJob && !selectedJob) {
      setSelectedJob(currentJob)
    }
  }, [currentJob, selectedJob])

  const handleSelectJob = (job: MusicJob) => {
    setSelectedJob(job)
    setCurrentJob(job)
  }

  const handleRetry = async (jobId: string) => {
    const job = await retryJob(jobId)
    if (job) {
      setSelectedJob(job)
    }
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold">AI 音樂生成</h1>
          <p className="text-muted-foreground">
            使用 Mureka AI 生成純音樂、歌曲或歌詞
          </p>
        </div>

        {/* Main content */}
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Left column - Form */}
          <div className="space-y-6 lg:col-span-1">
            {/* Quota display */}
            <QuotaDisplay />

            {/* Generation form */}
            <div className="rounded-lg border bg-card p-4">
              <h2 className="mb-4 text-lg font-semibold">新增生成</h2>
              <MusicForm />
            </div>
          </div>

          {/* Middle column - Job list */}
          <div className="lg:col-span-1">
            <MusicJobList
              onSelectJob={handleSelectJob}
              selectedJobId={selectedJob?.id}
            />
          </div>

          {/* Right column - Player */}
          <div className="lg:col-span-1">
            {selectedJob ? (
              <div>
                <h2 className="mb-4 text-lg font-semibold">詳細資訊</h2>
                <MusicPlayer job={selectedJob} onRetry={handleRetry} />
              </div>
            ) : (
              <div className="flex h-64 items-center justify-center rounded-lg border bg-muted/20 text-muted-foreground">
                選擇一個任務查看詳情
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MusicPage
