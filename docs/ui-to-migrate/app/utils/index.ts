export function randomInt(min: number, max: number): number {
  return Math.floor(Math.random() * (max - min + 1)) + min
}

export function randomFrom<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)]!
}

export const wellCapitalize = (text: string) => {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1)
}

export const googleDriveImageUrl = (id: string) => {
  return `https://drive.google.com/file/d/${id}/view`
}

export const imgcdnImageUrl = (id: string) => {
  return `https://s6.imgcdn.dev/${id}`
}
