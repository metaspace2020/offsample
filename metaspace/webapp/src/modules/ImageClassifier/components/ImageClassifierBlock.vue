<template>
  <intersect @change="handleVisibilityChange" :threshold="[0,0]" rootMargin="1000px">
    <div v-loading="loading">
      <div v-for="(row, idx) in rows"
           :key="idx"
           class="row">
        <div v-for="annotation in row"
             v-if="isVisible && annotation != null"
             :key="annotation.id"
             :data-key="annotation.id"
             :class="getAnnotationClass(annotation.id)"
             @mouseenter="e => $emit('mouseenter', Object.assign(e, {annotationId: annotation.id}))"
             @mouseleave="e => $emit('mouseleave', Object.assign(e, {annotationId: annotation.id}))"
        >
          <image-loader :src="annotation.isotopeImages[0].url"
                        :colormap="colormap"
                        :max-height="184"
                        :annotImageOpacity="1"
                        opticalSrc=""
                        opticalImageUrl=""
                        opacityMode="constant"
                        :showOpticalImage="false"
                        style="overflow: hidden;"
            />
          <div class="subtitle">
            <div>{{annotation.sumFormula}}</div>
            <div>{{ parseFloat(annotation.mz).toFixed(3) }}</div>
          </div>
        </div>
        <div v-else />
      </div>
      <hr />
    </div>
  </intersect>
</template>
<script lang="ts">
  import Vue from 'vue';
  import { Component, Prop } from 'vue-property-decorator';
  import gql from 'graphql-tag';
  import {debounce} from 'lodash-es';
  import Intersect from 'vue-intersect';
  import ImageLoader from '../../../components/ImageLoader.vue';

  const allAnnotationsQuery = gql`query AllAnnotations($filter: AnnotationFilter, $datasetFilter: DatasetFilter,
                                                       $offset: Int, $limit: Int) {
    allAnnotations(filter: $filter, datasetFilter: $datasetFilter,
                   offset: $offset, limit: $limit, orderBy: ORDER_BY_MZ, sortingOrder: ASCENDING) {
        id
        sumFormula
        adduct
        msmScore
        fdrLevel
        mz
        isotopeImages {
          mz
          url
          minIntensity
          maxIntensity
          totalIntensity
        }
      }
  }`;

  interface MzImage {
    mz: number;
    url: string;
    totalIntensity: number;
    minIntensity: number;
    maxIntensity: number;
  }

  interface Annotation {
    id: string;
    sumFormula: string;
    adduct: string;
    msmScore: number;
    fdrLevel: number;
    mz: number;
    isotopeImages: MzImage[];
  }
  type AnnotationLabel = undefined | 1 | 2 | 3;

  @Component({
    components: {
      Intersect,
      ImageLoader,
    },
    apollo: {
      allAnnotations: {
        query: allAnnotationsQuery,
        variables(this: ImageClassifierBlock) {
          return {
            offset: this.offset,
            limit: this.limit,
            ...this.gqlFilter,
          };
        },
        loadingKey: 'loading',
        skip(this: ImageClassifierBlock) {
          return !this.isVisible;
        }
      },
    },
  })
  export default class ImageClassifierBlock extends Vue {
    constructor() {
      super();
      this.handleVisibilityChange = debounce(this.handleVisibilityChange, 1000);
    }
    @Prop({ default: 'Viridis' })
    colormap!: string;
    @Prop()
    offset!: number;
    @Prop()
    limit!: number;
    @Prop()
    gqlFilter: any;
    @Prop()
    numCols!: number;
    @Prop()
    annotationLabels!: Record<string, AnnotationLabel>;

    loading = 0;
    isVisible = false;
    allAnnotations?: Annotation[];

    get rows(): (Annotation | null)[][] {
      const rows = [];
      for (let i = 0; i < Math.floor(this.limit / this.numCols); i++) {
        let annotations: (Annotation | null)[] = this.allAnnotations != null
          ? this.allAnnotations.slice(i * this.numCols, (i + 1) * this.numCols)
          : [];
        // Pad rows so they're all the same width
        while (annotations.length < this.numCols) {
          annotations.push(null);
        }
        rows.push(annotations);
      }
      return rows;
    }

    getAnnotationClass(id: string) {
      const label = this.annotationLabels[id];
      return {
        'annotation': true,
        'onsample': label === 1,
        'offsample': label === 2,
        'indeterminate': label === 3,
      }
    }

    handleVisibilityChange(intersection: IntersectionObserverEntry[]) {
      this.isVisible = intersection[0].isIntersecting;
      console.log(`${this.isVisible ? 'showing' : 'hiding'} block ${this.offset}`, intersection);
    }
  }
</script>
<style scoped lang="scss">
  .row {
    width: 100%;
    height: 250px;
    display: flex;
  }
  .annotation {
    height: 234px;
    max-width: 300px;
    flex: 1 1 200px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin: 8px;

    &.onsample {
      background-color: #CCFFCC;
    }
    &.offsample {
      background-color: #FFCCCC;
    }
    &.indeterminate {
      background-color: #DDDDDD;
    }
  }

  .subtitle {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    > * {
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      word-break: break-all;
      margin: 0 4px;
    }
  }
</style>
