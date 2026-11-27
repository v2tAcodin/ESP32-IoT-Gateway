/* USER CODE BEGIN Header */
/**
 ******************************************************************************
 * @file           : main.c
 * @brief          : Main program body
 ******************************************************************************
 * @attention
 *
 * Copyright (c) 2026 STMicroelectronics.
 * All rights reserved.
 *
 * This software is licensed under terms that can be found in the LICENSE file
 * in the root directory of this software component.
 * If no LICENSE file comes with this software, it is provided AS-IS.
 *
 ******************************************************************************
 */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "gpio.h"
#include "adc.h"
#include "usart.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdio.h>
#include <string.h>
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define NUM_SAMPLES 20
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
// --- CẤU HÌNH THANG ĐO CẢM BIẾN MỨC NƯỚC (0 - 5M, 0 - 3.3V) ---
#define SENSOR_ZERO_OFFSET_VOLTAGE 0.12f // Điện áp ban đầu khi ở ngoài không khí (0cm)
#define SENSOR_MAX_VOLTAGE         3.30f // Điện áp ngõ ra lớn nhất của cảm biến (V)
#define SENSOR_MAX_WATER_LEVEL_CM  500.0f// Chiều cao mức nước tối đa: 5 mét = 500 cm
#define ADC_SAMPLE_COUNT           32    // Tăng lên 32 mẫu để khử nhiễu tốt hơn

// Hệ số quy đổi áp suất sang cột nước: 1 Bar = 1019.72 cm H2O (P = rho * g * h)
#define BAR_TO_CM_WATER            1019.72f

// Biến lưu trữ giá trị đo
volatile uint32_t g_adc_raw = 0;
volatile float g_voltage = 0.0f;
volatile float g_pressure_bar = 0.0f;
volatile float g_pressure_kpa = 0.0f;
volatile float g_water_level_cm = 0.0f; // Mức nước tính bằng centimet (cm)
/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
// Hàm đọc giá trị ADC trung bình 32 mẫu liên tục
uint32_t Read_ADC_Filtered(void) {
  uint32_t sum = 0;
  for (int i = 0; i < ADC_SAMPLE_COUNT; i++) {
    HAL_ADC_Start(&hadc1);
    if (HAL_ADC_PollForConversion(&hadc1, 10) == HAL_OK) {
      sum += HAL_ADC_GetValue(&hadc1);
    }
    HAL_ADC_Stop(&hadc1);
  }
  return (sum / ADC_SAMPLE_COUNT);
}
/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{

  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_ADC1_Init();
  MX_USART1_UART_Init();
  /* USER CODE BEGIN 2 */
  // 1. Hiệu chuẩn ADC1 trên STM32F1
  HAL_ADCEx_Calibration_Start(&hadc1);
  /* USER CODE END 2 */

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1) {
    // --- BƯỚC 1: ĐỌC DỮ LIỆU TỪ CẢM BIẾN ---
    g_adc_raw = Read_ADC_Filtered();

    // --- BƯỚC 2: TÍNH ĐIỆN ÁP, MỨC NƯỚC (CM) & ÁP SUẤT ---
    // Điện áp thực tế đo được tại chân ADC (0V - 3.3V)
    g_voltage = ((float)g_adc_raw / 4095.0f) * 3.3f;

    // Trừ hao điện áp ban đầu (0.12V) khi ở ngoài không khí
    float v_effective = g_voltage - SENSOR_ZERO_OFFSET_VOLTAGE;
    if (v_effective < 0.0f) {
      v_effective = 0.0f; // Tránh ra số âm khi điện áp hơi dao động quanh 0.12V
    }

    // Dải điện áp hoạt động thực tế từ 0.12V (ứng với 0cm) đến 3.30V (ứng với 500cm)
    float voltage_span = SENSOR_MAX_VOLTAGE - SENSOR_ZERO_OFFSET_VOLTAGE;

    // Tính trực tiếp chiều cao mức nước thô theo tỉ lệ tuyến tính
    float raw_level_cm = (v_effective / voltage_span) * SENSOR_MAX_WATER_LEVEL_CM;
    if (raw_level_cm > SENSOR_MAX_WATER_LEVEL_CM) {
      raw_level_cm = SENSOR_MAX_WATER_LEVEL_CM;
    }

    // 1. Bộ lọc thông thấp số thích nghi (Adaptive EMA filter):
    // - Khi có biến động lớn (> 2.0cm, ví dụ khi nhúng/rút cảm biến khỏi nước): bắt kịp ngay lập tức!
    // - Khi dao động nhỏ: dùng bộ lọc 85% cũ + 15% mới để triệt tiêu sóng nước và nhiễu ADC
    static float s_ema_level = -1.0f;
    if (s_ema_level < 0.0f) {
      s_ema_level = raw_level_cm;
    } else {
      float step = raw_level_cm - s_ema_level;
      if (step < 0.0f) step = -step;
      if (step > 2.0f) {
        // Biến động lớn: cập nhật ngay để nhảy vọt bắt kịp giá trị thực tức thì
        s_ema_level = 0.20f * s_ema_level + 0.80f * raw_level_cm;
      } else {
        // Biến động nhỏ: lọc phẳng mượt mà, triệt nhiễu
        s_ema_level = 0.85f * s_ema_level + 0.15f * raw_level_cm;
      }
    }

    // 2. Bộ lọc chống rung số thập phân (Deadband filter 0.2cm):
    // Nếu mức nước dao động nhỏ hơn 0.2cm thì khóa số hiển thị, tránh nhảy số liên tục
    float diff = s_ema_level - g_water_level_cm;
    if (diff < 0.0f) {
      diff = -diff;
    }
    if (diff >= 0.2f || g_water_level_cm == 0.0f) {
      g_water_level_cm = s_ema_level;
    }

    // Quy đổi mức nước sang áp suất thủy tĩnh: P = rho * g * h (1 Bar = 1019.72 cm H2O)
    g_pressure_bar = g_water_level_cm / BAR_TO_CM_WATER;

    // Quy đổi thêm đơn vị kPa (1 Bar = 100 kPa)
    g_pressure_kpa = g_pressure_bar * 100.0f;

    // --- BƯỚC 3: TRUYỀN DỮ LIỆU SANG ESP32-C3 ĐỊNH KỲ 5 GIÂY (NON-BLOCKING) ---
    static uint32_t s_last_tx_tick = 0;
    uint32_t now_tick = HAL_GetTick();

    // Gửi ngay gói đầu tiên, sau đó cứ mỗi 5000ms (5 giây) gửi 1 lần sang ESP32
    if (s_last_tx_tick == 0 || (now_tick - s_last_tx_tick) >= 5000) {
      s_last_tx_tick = now_tick;

      char uart_tx_buf[140];
      float water_percent = (g_water_level_cm / SENSOR_MAX_WATER_LEVEL_CM) * 100.0f;
      if (water_percent > 100.0f) water_percent = 100.0f;
      if (water_percent < 0.0f) water_percent = 0.0f;
      snprintf(uart_tx_buf, sizeof(uart_tx_buf), 
               "{\"level\":%.1f,\"volt\":%.2f,\"percent\":%.1f,\"press\":%.3f,\"raw\":%lu}\n", 
               g_water_level_cm, g_voltage, water_percent, g_pressure_bar, g_adc_raw);
      HAL_UART_Transmit(&huart1, (uint8_t*)uart_tx_buf, strlen(uart_tx_buf), 100);

      // Nháy LED PC13 mỗi khi gửi xong 1 gói tin
      HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
    }

    HAL_Delay(100); // Lấy mẫu & lọc số liên tục mỗi 100ms (cực nhạy, cập nhật tức thì)
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  /** Initializes the CPU, AHB and APB buses clocks
  */
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

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1) {
  }
  /* USER CODE END Error_Handler_Debug */
}
#ifdef USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line
     number, ex: printf("Wrong parameters value: file %s on line %d\r\n", file,
     line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */
