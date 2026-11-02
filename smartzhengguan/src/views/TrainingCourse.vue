<template>
  <FeatureWorkspace v-if="config" :config="config" />
</template>

<script>
import FeatureWorkspace from '../components/FeatureWorkspace.vue'
import { getTrainingCourseData } from '../services/mockDataService'

export default {
  components: { FeatureWorkspace },
  data() {
    return {
      config: null,
    }
  },
  async mounted() {
    this.config = await getTrainingCourseData()
  },
}
</script>
