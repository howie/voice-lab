/**
 * Voice Management Page
 *
 * Feature: 013-tts-role-mgmt
 * T020: Main page for managing TTS voice customizations
 */

import { VoiceManagementTable } from '@/components/voice-management'

export function VoiceManagementPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          角色管理
        </h1>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          自訂 TTS 角色的顯示名稱、收藏常用角色、隱藏不需要的角色
        </p>
      </div>

      {/* Table */}
      <VoiceManagementTable />
    </div>
  )
}
