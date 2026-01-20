# HW06 – Report

> Файл: `homeworks/HW06/report.md`  
> Важно: не меняйте названия разделов (заголовков). Заполняйте текстом и/или вставляйте результаты.

## 1. Dataset

- Какой датасет выбран: `S06-hw-dataset-01.csv`  
- Размер: (12000, 30)
- Целевая переменная: `target`  
  - Классы: 0 и 1  
  - Доли: 0 – 0.68, 1 – 0.32  
- Признаки: все числовые, столбцы `id` и `target` исключены из признаков

## 2. Protocol

- Разбиение: train/test = 0.8/0.2, `random_state=42`, стратификация по `target`  
- Подбор: GridSearchCV на train, 5 фолдов, оптимизация ROC-AUC для DecisionTree, RandomForest и GradientBoosting
- Метрики:  
  - Accuracy – доля верных предсказаний, удобно сравнивать все модели  
  - F1 – баланс precision и recall для дисбалансного бинарного таргета  
  - ROC-AUC – оценка способности модели разделять классы независимо от порога

## 3. Models

Сравнивались следующие модели:

- **DummyClassifier** (baseline, стратегия `most_frequent`)  
- **LogisticRegression** (baseline, Pipeline с StandardScaler)  
- **DecisionTreeClassifier** (контроль сложности: `max_depth`, `min_samples_leaf`, подбор через CV)  
- **RandomForestClassifier** (подбор `max_depth`, `min_samples_leaf`, 100 деревьев)  
- **GradientBoostingClassifier** (подбор `n_estimators`, `learning_rate`, глубина 3)  

Все модели оценены на test один раз после CV (для дерева и леса).  

## 4. Results

| Model                  | Accuracy | F1     | ROC-AUC |
|------------------------|----------|--------|---------|
| DummyClassifier        | 0.677    | 0.0    | 0.5     |
| LogisticRegression     | 0.828    | 0.708  | 0.875   |
| DecisionTreeClassifier | 0.877    | 0.800  | 0.907   |
| RandomForestClassifier | 0.912    | 0.852  | 0.958   |
| GradientBoosting       | 0.916    | 0.863  | 0.961   |

**Победитель:** GradientBoostingClassifier по ROC-AUC и F1; показывает наилучшее разделение классов и баланс precision/recall.

## 5. Analysis

- **Устойчивость:** при изменении `random_state` на несколько прогонов результаты RandomForest и GradientBoosting меняются незначительно, показатели остаются высокими
- **Ошибки:** confusion matrix для GradientBoosting показывает, что большее кол-во ошибок в процентном соотношении приходится на класс 1 
- **Интерпретация:** топ-10 признаков по permutation importance: `num18`, `num19`, `num07`, `num04`, `num24`, `num20`, `num01`, `num22`, `num21`, `num14`. Модель делает упор на несколько ключевых признаков, их перестановка сильно снижает качество, что делает предсказания интерпретируемыми.

## 6. Conclusion

- DummyClassifier показывает, что naive baseline малоинформативен для дисбалансного таргета.  
- LogisticRegression даёт хороший baseline, но ансамбли значительно лучше.  
- DecisionTree легко переобучается, контроль глубины и min_samples_leaf критичен.  
- RandomForest и GradientBoosting стабильно показывают высокие ROC-AUC и F1, их ансамблевая природа уменьшает переобучение.  
- Честный ML-протокол: CV на train, один раз test для финальной оценки, стратификация и фиксация random_state обеспечивают воспроизводимость и корректную оценку качества модели.
