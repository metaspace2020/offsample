<template>
  <div
    ref="container"
    :tabindex="0"
    @keydown="handleKeyDown"
    @keyup="handleKeyUp"
    @mouseenter="$refs.container.focus()"
  >
    <div class="header">
      <filter-panel level="imageclassifier" />
    </div>
    <div class="list" v-loading="loading">
      <image-classifier-block
        v-for="(block, idx) in blocks"
        :key="idx"
        v-bind="block"
        :gqlFilter="gqlFilter"
        :numCols="numCols"
        :annotationLabels="annotationLabels"
        @mouseenter="handleMouseEnter"
        @mouseleave="handleMouseLeave"
      />
    </div>
  </div>
</template>
<script lang="ts">
  import Vue from 'vue';
  import { Component } from 'vue-property-decorator';
  import gql from 'graphql-tag';
  import FilterPanel from '../../../components/FilterPanel.vue';
  import ImageClassifierBlock from './ImageClassifierBlock.vue';

  const countAnnotationsQuery = gql`query CountAnnotations($filter: AnnotationFilter, $datasetFilter: DatasetFilter) {
    countAnnotations(filter: $filter, datasetFilter: $datasetFilter)
  }`;

  const onKeys = ['v','f','CTRL'];
  const offKeys = ['c','d','SHIFT'];
  const indKeys = ['x','s']; // or both an onKey and offKey
  const undoKeys = ['z','a'];
  const keysToPrevent = [].concat(onKeys, offKeys, indKeys, undoKeys);

  @Component({
    components: {
      ImageClassifierBlock,
      FilterPanel,
    },
    apollo: {
      countAnnotations: {
        query: countAnnotationsQuery,
        variables(this: ImageClassifierPage) {
          return this.gqlFilter;
        },
        loadingKey: 'loading'
      },
    },
  })
  export default class ImageClassifierPage extends Vue {
    loading = 0;
    numCols = 4;
    countAnnotations?: number;
    keys: Record<string, boolean> = {};
    overAnnotationId: string | null = null;
    annotationLabels: Record<string, number> = {};

    created() {
      // document.addEventListener('keydown', this.handleKeyDown);
      // document.addEventListener('keyup', this.handleKeyUp);
      // document.addEventListener('mousedown', this.handleMouseDown);
      // document.addEventListener('mouseup', this.handleMouseUp);
    }
    mounted() {
      (this.$refs.container as any).focus();
    }
    beforeDestroy() {
      // document.removeEventListener('keydown', this.handleKeyDown);
      // document.removeEventListener('keyup', this.handleKeyUp);
      // document.addEventListener('mousedown', this.handleMouseDown);
      // document.addEventListener('mouseup', this.handleMouseUp);
    }

    get gqlFilter () {
      return {
        filter: this.$store.getters.gqlAnnotationFilter,
        datasetFilter: this.$store.getters.gqlDatasetFilter,
      };
    }

    get blocks() {
      const blockSize = 100;
      const block = [];
      for (let i = 0; i < (this.countAnnotations || 0); i += blockSize) {
        block.push({ offset: i, limit: Math.min(blockSize, (this.countAnnotations || 0) - i) })
      }
      return block;
    }
    get datasetFilter() {
      return { ids: '2016-12-09_10h16m23s' };
    }

    handleKeyDown(event: KeyboardEvent) {
      this.keys[event.key] = true;
      if (keysToPrevent.includes(event.key)) {
        event.preventDefault();
      }
      this.doSelection();
    }

    handleKeyUp(event: KeyboardEvent) {
      this.keys[event.key] = false;
      if (keysToPrevent.includes(event.key)) {
        event.preventDefault();
      }
    }

    handleMouseEnter(event: MouseEvent & { annotationId: string }) {
      this.overAnnotationId = event.annotationId;
      this.doSelection();
    }

    handleMouseLeave(event: MouseEvent & { annotationId: string }) {
      if (this.overAnnotationId == event.annotationId) {
        this.overAnnotationId = null;
      }
    }

    doSelection() {
      if (this.overAnnotationId) {
        const on = onKeys.some(key => this.keys[key]);
        const off = offKeys.some(key => this.keys[key]);
        const ind = (on && off) || indKeys.some(key => this.keys[key]);
        const undo = undoKeys.some(key => this.keys[key]);

        if (on || off || ind || undo) {
          const val = undo ? null : ind ? 3 : on ? 1 : 2;
          Vue.set(this.annotationLabels, this.overAnnotationId, val);
        }
      }
    }
  }
</script>
<style scoped lang="scss">

</style>
