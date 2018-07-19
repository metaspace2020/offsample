<template>
  <div
    ref="container"
    :tabindex="0"
    @keydown="handleKeyDown"
    @keyup="handleKeyUp"
    @mouseenter="$refs.container.focus()"
    @mousedown="handleMouseDown"
    @contextmenu.prevent
  >
    <div class="header">
      <filter-panel level="imageclassifier" />
      <ul>
        <li>Left-click, V or F to mark an image as <span style="background-color: #CCFFCC" >on-sample</span></li>
        <li>Right-click, C or D to mark an image as <span style="background-color: #FFCCCC" >off-sample</span></li>
        <li>both mouse buttons, X or S to mark an image as <span style="background-color: #FFFFCC" >unknown</span></li>
        <li>Z or A to unmark an image</li>
        <li>You can click-and-drag or press a key and sweep your mouse across multiple images to mark them quickly</li>
      </ul>
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
    <div v-if="countAnnotations === 0">
      Please select a dataset.
    </div>
  </div>
</template>
<script lang="ts">
  import Vue from 'vue';
  import { Component, Watch } from 'vue-property-decorator';
  import gql from 'graphql-tag';
  import FilterPanel from '../../../components/FilterPanel.vue';
  import ImageClassifierBlock from './ImageClassifierBlock.vue';
  import * as config from '../../../clientConfig.json';

  const countAnnotationsQuery = gql`query CountAnnotations($filter: AnnotationFilter, $datasetFilter: DatasetFilter) {
    countAnnotations(filter: $filter, datasetFilter: $datasetFilter)
  }`;

  const onKeys = ['v','f','CTRL', 'MOUSE0'];
  const offKeys = ['c','d','SHIFT', 'MOUSE2'];
  const indKeys = ['x','s']; // or both an onKey and offKey
  const undoKeys = ['z','a'];
  const keysToPrevent = [...onKeys, ...offKeys, ...indKeys, ...undoKeys];

  const qs = (obj: Object) => '?' + Object.entries(obj)
    .map(([key, val]) => `${encodeURIComponent(key)}=${encodeURIComponent(val)}`)
    .join('&');

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
        loadingKey: 'loading',
        skip(this: ImageClassifierPage) {
          if (!this.datasetId || !this.user) {
            this.countAnnotations = 0;
            return true;
          }
          return false;
        }
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
      this.loadLabels();
      document.addEventListener('mouseup', this.handleMouseUp);
    }
    mounted() {
      (this.$refs.container as any).focus();
    }
    beforeDestroy() {
      document.removeEventListener('mouseup', this.handleMouseUp);
    }

    get gqlFilter () {
      return {
        filter: this.$store.getters.gqlAnnotationFilter,
        datasetFilter: this.$store.getters.gqlDatasetFilter,
      };
    }

    get blocks() {
      const blockSize = 12;
      const block = [];
      for (let i = 0; i < (this.countAnnotations || 0); i += blockSize) {
        block.push({ offset: i, limit: Math.min(blockSize, (this.countAnnotations || 0) - i) })
      }
      return block;
    }
    get datasetId(): string {
      return this.$store.getters.gqlDatasetFilter.ids;
    }
    get user(): string {
      return this.$route.query.user;
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
      this.doSelection();
    }

    handleMouseDown(event: MouseEvent) {
      const key = `MOUSE${event.button}`;
      this.keys[key] = true;
      if (keysToPrevent.includes(key)) {
        event.preventDefault();
      }
      this.doSelection();
    }

    handleMouseUp(event: MouseEvent) {
      const key = `MOUSE${event.button}`;
      if (this.keys[key]) {
        this.keys[key] = false;
        if (keysToPrevent.includes(key)) {
          event.preventDefault();
        }
      }
      this.doSelection();
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

    async doSelection() {
      if (this.overAnnotationId) {
        const on = onKeys.some(key => this.keys[key]);
        const off = offKeys.some(key => this.keys[key]);
        const ind = (on && off) || indKeys.some(key => this.keys[key]);
        const undo = undoKeys.some(key => this.keys[key]);

        if (on || off || ind || undo) {
          const type = undo ? null : ind ? 3 : on ? 1 : 2;
          if (this.annotationLabels[this.overAnnotationId] !== type) {
            const query = qs({
              datasetId: this.datasetId,
              user: this.user,
              annotationId: this.overAnnotationId,
              type
            });
            Vue.set(this.annotationLabels, this.overAnnotationId, type);
            try {
              await fetch(`${config.imageClassifierUrl}${query}`, { method: 'POST' });
            } catch (err) {
              this.$alert(err, "Something went terribly wrong");
              Vue.set(this.annotationLabels, this.overAnnotationId, 4);
            }
          }
        }
      }
    }

    @Watch('datasetId')
    @Watch('user')
    async loadLabels() {
      const datasetId = this.datasetId;
      const user = this.user;

      if (datasetId && user) {
        const query = qs({ datasetId, user });
        try {
          this.loading += 1;
          const response = await fetch(`${config.imageClassifierUrl}${query}`);
          const labels = await response.json();
          // Double-check nothing has changed while loading
          if (datasetId === this.datasetId && user === this.user) {
            this.annotationLabels = labels;
          }
        } catch (err) {
          console.log(err);
          if (datasetId === this.datasetId && user === this.user) {
            this.annotationLabels = {};
            this.$alert("Could not load previous classifications")
          }
        } finally {
          this.loading -= 1;
        }
      } else {
        this.annotationLabels = {};
      }
    }
  }
</script>
<style scoped lang="scss">

</style>
