#include "main.h"
#include "gpio.h"
#include "usart.h"
#include "adc.h"
#include <stdio.h>
#include <string.h>

void SystemClock_Config(void);

#define ADC_SAMPLE_COUNT 16 // Lấy mẫu 16 lần tính trung bình để khử nhiễu tiếp xúc biến trở

/**
 * @brief Đọc giá trị ADC trung bình từ chân PA0
 */
uint32_t Read_ADC_Averaged(void)
{
  uint32_t sum = 0;
  for (int i = 0; i < ADC_SAMPLE_COUNT; i++)
  {
    HAL_ADC_Start(&hadc1);
    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK)
    {
      sum += HAL_ADC_GetValue(&hadc1);
    }
    HAL_ADC_Stop(&hadc1);
  }
  return (sum / ADC_SAMPLE_COUNT);
}

int main(void)
{
  /* 1. Khởi tạo hệ thống */
  HAL_Init();
  SystemClock_Config();

  /* 2. Khởi tạo ngoại vi: LED PC13, ADC1 (PA0), UART1 (PA9 TX, PA10 RX) */
  MX_GPIO_Init();
  MX_ADC1_Init();
  MX_USART1_UART_Init();

  /* Hiệu chuẩn ADC (Rất quan trọng trên STM32F1 để đọc điện áp chính xác) */
  HAL_ADCEx_Calibration_Start(&hadc1);

  /* Nhấp nháy LED PC13 2 lần báo hiệu STM32 đã khởi động xong */
  for (int i = 0; i < 2; i++) {
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_RESET); // Bật LED
    HAL_Delay(100);
    HAL_GPIO_WritePin(GPIOC, GPIO_PIN_13, GPIO_PIN_SET);   // Tắt LED
    HAL_Delay(100);
  }

  uint32_t sample_counter = 0;

  /* Vòng lặp chính */
  while (1)
  {
    /* 1. Đọc giá trị ADC từ chân PA0 (Độ phân giải 12-bit: 0 -> 4095) */
    uint32_t raw_adc = Read_ADC_Averaged();

    /* 2. Quy đổi sang mức điện áp thực tế (0.00V -> 3.30V) */
    // Công thức: Vout = (ADC_RAW / 4095.0) * 3.30V
    float voltage = ((float)raw_adc / 4095.0f) * 3.30f;

    /* 3. Quy đổi sang phần trăm góc xoay biến trở (0% -> 100%) */
    float percent = ((float)raw_adc / 4095.0f) * 100.0f;

    sample_counter++;

    /* 4. Nháy nhẹ đèn LED PC13 để biết STM32 đang truyền dữ liệu */
    HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);

    /* 5. Đóng gói chuỗi JSON (Bắt buộc có '\n' ở cuối để ESP32 nhận diện gói tin) */
    char tx_buffer[128];
    int len = snprintf(tx_buffer, sizeof(tx_buffer),
                       "{\"volt\":%.2f,\"percent\":%.1f,\"raw\":%lu}\n",
                       voltage, percent, (unsigned long)raw_adc);

    /* 6. Gửi dữ liệu qua UART1 (PA9 TX) sang ESP32-C3 */
    HAL_UART_Transmit(&huart1, (uint8_t*)tx_buffer, len, 100);

    /* 7. Chu kỳ lấy mẫu và gửi (500ms / lần = 2 lần mỗi giây) */
    HAL_Delay(500);
  }
}

/**
  * @brief Cấu hình Clock hệ thống
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

void Error_Handler(void)
{
  __disable_irq();
  while (1)
  {
  }
}
