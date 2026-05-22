import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
    selector: 'app-profile-menu-item',
    standalone: true,
    imports: [CommonModule],
    template: `
    <button 
      (click)="itemClick.emit()"
      [ngClass]="{
        'w-full flex items-center gap-4 px-6 py-4 rounded-2xl transition-all duration-200 group/item text-left': true,
        'hover:bg-gray-50 text-gray-500 hover:text-poke-blue': variant === 'normal',
        'hover:bg-red-50 text-gray-500 hover:text-red-600': variant === 'danger'
      }"
    >
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        fill="none" 
        viewBox="0 0 14 14" 
        class="w-5 h-5 fill-current transition-colors"
      >
        <path 
          [attr.d]="svgPath" 
          [attr.fill-rule]="fillRule" 
          [attr.clip-rule]="clipRule" 
          stroke-width="1"
        ></path>
      </svg>
      
      <div *ngIf="subtitle; else simpleLabel" class="flex flex-col text-left">
        <span class="text-xl font-medium leading-none">{{ label }}</span>
        <span class="text-xs text-gray-400 font-normal mt-1">{{ subtitle }}</span>
      </div>
      
      <ng-template #simpleLabel>
        <span class="text-xl font-medium">{{ label }}</span>
      </ng-template>
    </button>
  `,
    styles: []
})
export class ProfileMenuItemComponent {
    @Input() label: string = '';
    @Input() subtitle?: string;
    @Input() svgPath: string = '';
    @Input() fillRule: string = 'evenodd';
    @Input() clipRule: string = 'evenodd';
    @Input() variant: 'normal' | 'danger' = 'normal';
    @Output() itemClick = new EventEmitter<void>();
}
