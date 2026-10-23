<template>
  <!-- 全量 app.use(ElementPlus, { locale }) 移除后，中文语言包改由 ConfigProvider 提供，
       否则分页/日期选择器等内置文案会回退成英文。 -->
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup>
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
#app {
  height: 100%;
}
</style>
