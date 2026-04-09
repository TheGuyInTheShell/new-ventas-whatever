<script setup lang="ts">
import { z } from 'zod'
import type { FormSubmitEvent } from '#ui/types'

definePageMeta({
  layout: 'auth'
})

const { signIn, verifyOtp } = useAuth()
const toast = useToast()
const router = useRouter()

const isOtpStep = ref(false)
const isLoading = ref(false)
const tempToken = ref('') // To store the temp token for 2FA

// Schema for Login
const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required')
})

type LoginSchema = z.output<typeof loginSchema>

const loginState = reactive({
  username: '',
  password: ''
})

// Schema for OTP
const otpSchema = z.object({
  otp: z.string().length(6, 'Must be 6 digits')
})

type OtpSchema = z.output<typeof otpSchema>

const otpState = reactive({
  otp: ''
})

async function onLoginSubmit(event: FormSubmitEvent<LoginSchema>) {
  isLoading.value = true
  try {
    const result = await signIn(event.data.username, event.data.password)

    if (!result) {
      throw new Error('Login failed')
    }

    if (result.status === '2fa_required') {
      tempToken.value = result.temp_token ?? ''
      isOtpStep.value = true
      toast.add({ title: '2FA Required', description: 'Please enter your OTP code.' })
    } else {
      toast.add({ title: 'Welcome back!' })
      router.push('/')
    }
  } catch (error: any) {
    console.error(error)
    toast.add({
      title: 'Login Failed',
      description: error.data?.detail || error.message || 'An error occurred',
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

async function onOtpSubmit(event: FormSubmitEvent<OtpSchema>) {
  isLoading.value = true
  try {
    await verifyOtp(event.data.otp, tempToken.value)
    toast.add({ title: 'Verified!', description: 'Redirecting...' })
    router.push('/')
  } catch (error: any) {
    toast.add({
      title: 'Verification Failed',
      description: error.data?.detail || 'Invalid OTP code',
      color: 'error'
    })
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <UCard class="w-full max-w-sm">
    <template #header>
      <div class="text-center">
        <h1 class="text-xl font-bold">
          {{ isOtpStep ? 'Two-Factor Authentication' : 'Sign In' }}
        </h1>
        <p class="text-gray-500 text-sm mt-1">
          {{ isOtpStep ? 'Enter the code from your authenticator app.' : 'Welcome back! Please sign in to continue.' }}
        </p>
      </div>
    </template>

    <!-- Login Form -->
    <UForm
      v-if="!isOtpStep"
      :schema="loginSchema"
      :state="loginState"
      class="space-y-4 flex flex-col items-center justify-center"
      @submit="onLoginSubmit"
    >
      <UFieldGroup class="w-full" label="Username" name="username">
        <UInput
          id="username"
          v-model="loginState.username"
          class="w-full"
          color="primary"
          size="xl"
          placeholder="Username"
        />
      </UFieldGroup>

      <UFieldGroup class="w-full" label="Password" name="password">
        <UInput
          id="password"
          v-model="loginState.password"
          class="w-full"
          color="primary"
          type="password"
          size="xl"
          placeholder="Password"
        />
      </UFieldGroup>

      <UButton
        type="submit"
        color="primary"
        block
        :loading="isLoading"
      >
        Sign In
      </UButton>
    </UForm>

    <!-- OTP Form -->
    <UForm
      v-else
      :schema="otpSchema"
      :state="otpState"
      class="space-y-4 flex flex-col items-center justify-center"
      @submit="onOtpSubmit"
    >
      <UFieldGroup class="w-full" label="OTP Code" name="otp">
        <UInput
          v-model="otpState.otp"
          class="w-full"
          color="primary"
          placeholder="123456"
          autofocus
          size="xl"
        />
      </UFieldGroup>

      <UButton type="submit" block :loading="isLoading">
        Verify
      </UButton>

      <UButton
        variant="ghost"
        block
        class="mt-2"
        @click="isOtpStep = false"
      >
        Back to Login
      </UButton>
    </UForm>
  </UCard>
</template>
